#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pyplr.oceanops
==============

A module to help with measurents for Ocean Optics spectrometers.

"""
import os.path as op
from time import sleep
from typing import Tuple, List, Union, Optional, Any
from datetime import datetime

import numpy as np
from numpy import typing as npt
import pandas as pd
import matplotlib.pyplot as plt
from scipy import interpolate, signal
from seabreeze.spectrometers import Spectrometer


class OceanOptics(Spectrometer):
    """Extension for `seabreeze.spectrometers.Spectrometer`."""

    def __init__(self, device) -> None:
        super().__init__(device)

    def get_temperatures(self):
        """Get temperatures of the printed circuit board and microcontroller."""

        try:
            temps = self.f.temperature.temperature_get_all()
            sleep(0.01)
            board_temp = temps[0]
            micro_temp = temps[2]
        except Exception:
            board_temp = "NA"
            micro_temp = "NA"

        return (board_temp, micro_temp)

    def _print_sample_details(self, integration_time, max_reported):
        print(f"\t> Integration time: {int(integration_time) / 1e6} seconds")
        print(f"\t> Maximum reported value: {int(max_reported)}")

    def get_wavelength_spread(self, wls):
        return np.hstack(
            [(wls[1] - wls[0]), (wls[2:] - wls[:-2]) / 2, (wls[-1] - wls[-2])]
        )

    # User defined methods
    def sample(
        self,
        integration_time: Optional[Union[int, None]] = None,
        scans_to_average: Optional[int] = 1,
        boxcar_width: Optional[int] = 0,
        correct_dark_counts: Optional[bool] = False,
        correct_nonlinearity: Optional[bool] = False,
        wavelengths: Optional[npt.NDArray] = None,
        sample_id: Union[str, dict] = None,
        **kwargs,
    ) -> Tuple[pd.Series, dict]:
        """Obtain a sample with an Ocean Optics spectrometer.

        Parameters
        ----------
        integration_time : int, optional
            The integration time to use when obtaining the sample. If `None`,
            `integration_time` is adapted until the reported counts are 80-90%
            of the maximum intensity value for the device (where the response
            of the sensor is most linear). The default is `None`.
        scans_to_average : int, optional
            The number of scans to average before returning the sample. More
            scans increases the signal-to-noise-ratio, but also the overall
            sampling time. The default is 1.
        boxcar_width : int, optional
            Width of moving window for boxcar smoothing. Reduces noise by
            averaging the values of adjacent pixels, but at the expense of
            optical resolution, which is to say that higher values may wash out
            spectral features). The default is `0`.
        correct_dark_counts : bool, optional
            Pass `True` to remove the noise floor in measurements, if the spectrometer
            supports this feature. The default is `False`.
        correct_nonlinearity : bool, optional
            Correct the sample for non-linearty using on-board coefficients,
            if the spectrometer supports this feature. The default is `False`.
        sample_id : str or dict, optional
             Information identifying the sample, to be included in `info`. For
             example, `"daylight_spectrum"`, or `{'Primary' : 5, 'intensity' :
             3000}`. The default is `None`.
        wavelengths : array_like
            Option to override spectrometer wavelengths. May be useful if you
            performed a wavelength calibration but didn't get round to updating
            the spectrometer coefficients. The default is None.

        Returns
        -------
        counts : pd.Series
            The sample intensity counts.
        info : dict
            Companion info for measurement.

        """
        if sample_id is None:
            sample_id = "unnamed_sample"

        upper_bound = None
        lower_bound = None

        print("> Obtaining sample...")
        print(f"> Correcting for dark counts: {correct_dark_counts}")
        print(f"> Correcting for nonlinearity: {correct_nonlinearity}")

        if integration_time is not None:
            # Set the spectrometer integration time
            self.integration_time_micros(int(integration_time))
            sleep(0.01)

            # Obtain temperature measurements
            board_temp, micro_temp = self.get_temperatures()

            # Obtain intensity measurements
            counts = self.intensities(
                correct_dark_counts=correct_dark_counts,
                correct_nonlinearity=correct_nonlinearity,
            )

            # Get the maximum reported value
            max_reported = max(counts)
            self._print_sample_details(integration_time, max_reported)

        else:
            # Initial parameters. The CCD is most linear between 80-90%
            # saturation.
            maximum_intensity = self.max_intensity
            lower_bound = maximum_intensity * 0.8
            upper_bound = maximum_intensity * 0.9
            target = maximum_intensity * 0.85

            # Start with the minimum integration time available
            integration_time = min(self.integration_time_micros_limits)
            max_reported = 0

            # Keep sampling with different integration times until the maximum
            # reported value is within 80-90% of the maximum intensity value
            # for the device
            while (max_reported < lower_bound) or (max_reported > upper_bound):

                # If current integration time is greater than the upper limit,
                # set it to the upper limit
                if integration_time >= self.integration_time_micros_limits[1]:
                    integration_time = self.integration_time_micros_limits[1]

                # Set the spectrometer integration time
                self.integration_time_micros(int(integration_time))
                sleep(0.01)

                # Obtain temperature measurements if available
                board_temp, micro_temp = self.get_temperatures()

                # Obtain intensity measurements
                counts = self.intensities(
                    correct_dark_counts=correct_dark_counts,
                    correct_nonlinearity=correct_nonlinearity,
                )
                sleep(0.01)

                # Get the maximum reported value
                max_reported = max(counts)
                self._print_sample_details(integration_time, max_reported)

                # Adjust integration time for next iteration
                multiplier = target / counts.max()
                integration_time = integration_time * multiplier
                
        if scans_to_average > 1:
            print(f"> Computing average of {scans_to_average} scans")

            for scan in range(scans_to_average - 1):

                counts += self.intensities(  # Integration time is already set
                    correct_dark_counts=correct_dark_counts,
                    correct_nonlinearity=correct_nonlinearity,
                )
            counts /= scans_to_average

        # Boxcar averaging
        if boxcar_width > 0:
            print(f"> Applying boxcar average (boxcar_width = {boxcar_width})")

            counts = PostProcessor.smooth_spectrum_boxcar(
                counts, boxcar_width=boxcar_width
            )

        # Convert to series
        counts = pd.Series(counts, index=self.wavelengths(), name="Counts")
        if wavelengths is not None:
            counts.index = wavelengths
        counts.index.name = "Wavelength"
        
        # Prepare info dict
        info = {
            "board_temp": board_temp,
            "micro_temp": micro_temp,
            "integration_time": int(integration_time),
            "scans_averaged": scans_to_average,
            "boxcar_width": boxcar_width,
            "max_reported": counts.max(),
            "upper_bound": upper_bound,
            "lower_bound": lower_bound,
            "model": self.model,
            "serial": self.serial_number,
            "obtained": str(datetime.now()),
        }
        if isinstance(sample_id, dict):
            info.update(sample_id)
        else:
            info["sample_id"] = sample_id

        print("\n")

        return (
            counts,
            info,
        )


class PostProcessor:
    def __init__(
        self,
        spectra: pd.DataFrame,
        spectra_info: pd.DataFrame,
        calibration: Union[str, pd.Series],
        collection_area: float = 0.0012566370614359172,
    ) -> None:
        """


        Parameters
        ----------
        fiber_diameter : int
            Diameter of the fiber in microns. The default is None.
        calibration_file : Optional[Union[str, pd.Series]], optional
            DESCRIPTION. The default is None.

        Returns
        -------
        None

        """
        self.spectra = spectra
        self.spectra_info = spectra_info
        self.calibration = calibration
        self.collection_area = collection_area


    @staticmethod
    def smooth_spectrum_boxcar(spectrum, boxcar_width: int = 0) -> npt.NDArray:
        """Boxcar smoothing with zero-order savitsky golay filter."""
        window_length = (boxcar_width * 2) + 1
        return signal.savgol_filter(spectrum, window_length, polyorder=0)

    @staticmethod
    def resample_spectrum_wavelength(
        self, wavelengths, spectrum, desired_wavelengths
    ):
        """Resample spectrum to new wavelengths"""
        return interpolate.interp1d(wavelengths, spectrum)(desired_wavelengths)

    @staticmethod
    def get_wavelength_spread(wavelengths):
        """Return the wavelength spread of the spectrometer pixels"""
        return np.hstack(
            [
                (wavelengths[1] - wavelengths[0]),
                (wavelengths[2:] - wavelengths[:-2]) / 2,
                (wavelengths[-1] - wavelengths[-2]),
            ]
        )

    def calibrate_spectrum_irradiance(
        self, spectrum, integration_time, dark_counts=0
    ):
        integration_time /= 1e6
        return (spectrum - dark_counts) * (  # Already dark corrected
            self.calibration_file
            / (integration_time * self.collection_area * self.wavelength_spread)
        )


def predict_dark_counts(
    spectra_info: pd.DataFrame, darkcal: pd.DataFrame
) -> pd.DataFrame:
    """Predict dark counts from temperature and integration times.

    These get subtracted from measured pixel counts in
    `OceanOptics.calibrated_radiance(...)`

    Parameters
    ----------
    spectra_info : pd.DataFrame
        Spectra companion info containing the 'board_temp' and
        'integration_time' variables.
    darkcal : pd.DataFrame
        Parameters accounting for the relationship between PCB temperature and
        integration time and their effect on raw pixel counts. Currently
        generated in MATLAB.

    Returns
    -------
    pandas.DataFrame
        The predicted dark counts.

    """
    dark_counts = []

    for idx, row in spectra_info.iterrows():
        x = spectra_info.loc[idx, "board_temp"]
        y = spectra_info.loc[idx, "integration_time"]
        dark_spec = []

        for i in range(0, darkcal.shape[0]):
            p00 = darkcal.loc[i, "p00"]
            p10 = darkcal.loc[i, "p10"]
            p01 = darkcal.loc[i, "p01"]
            p20 = darkcal.loc[i, "p20"]
            p11 = darkcal.loc[i, "p11"]
            p30 = darkcal.loc[i, "p30"]
            p21 = darkcal.loc[i, "p21"]

            dark_spec.append(
                p00
                + p10 * x
                + p01 * y
                + p20 * x * x
                + p11 * x * y
                + p30 * x * x * x
                + p21 * x * x * y
            )

        dark_counts.append(dark_spec)

    # TODO: add code with function parameter to exclude poorly fitting pixels.
    # using a visually determined threshold, for now.
    FIT_RMSE_THRESHOLD = 110
    dark_counts = np.where(
        darkcal.rmse > FIT_RMSE_THRESHOLD, np.nan, dark_counts
    )

    return pd.DataFrame(dark_counts)


def calibrated_radiance(
    spectra: pd.DataFrame,
    spectra_info: pd.DataFrame,
    dark_counts: pd.DataFrame,
    cal_per_wl: pd.DataFrame,
    sensor_area: float,
) -> pd.DataFrame:
    """Convert raw OceanOptics data into calibrated radiance.

    Parameters
    ----------
    spectra : `pandas.DataFrame`
        Spectra to be calibrated, as returned by
        `OceanOptics.measurement(...)`. Column index must be spectrometer
        wavelength bins.
    spectra_info : `pandas.DataFrame`
        Spectra companion info, as returned by `OceanOptics.measurement(...)`.
    dark_counts : `pandas.DataFrame`
        Predicted dark counts for each pixel. See
        `OceanOptics.predict_dark_counts(...)`
    cal_per_wl : `pandas.DataFrame`
        Spectrometer calibration file.
    sensor_area : float
        Sensor area in cm2. Spectrometer constant.

    Returns
    -------
    w_per_m2_per_nm : `pandas.DataFrame`
        Calibrated radiance data in watts per meter squared units.

    """
    # we have no saturated spectra due to adaptive measurement
    # convert integration time from us to s
    spectra_info["integration_time"] = spectra_info["integration_time"] / (
        1000 * 1000
    )
    # float index for spectra columns
    spectra.columns = pd.Float64Index(spectra.columns)

    # borrow wavelength indices
    cal_per_wl.index = spectra.columns
    dark_counts.columns = spectra.columns

    # microjoules per pixel
    uj_per_pixel = (spectra - dark_counts) * cal_per_wl.T.values[0]

    # get the wavelengths and calculate the nm/pixel binwidth
    wls = uj_per_pixel.columns
    nm_per_pixel = np.hstack(
        [(wls[1] - wls[0]), (wls[2:] - wls[:-2]) / 2, (wls[-1] - wls[-2])]
    )

    # calculate microwatts per cm2 per nanometer
    uj_per_nm = uj_per_pixel / nm_per_pixel
    uj_per_cm2_per_nm = uj_per_nm / sensor_area
    uw_per_cm2_per_nm = uj_per_cm2_per_nm.div(
        spectra_info["integration_time"], axis="rows"
    )

    # Resample to visible spectrum in 1 nm bins
    uw_per_cm2_per_nm = uw_per_cm2_per_nm.to_numpy()
    f = interpolate.interp1d(wls, uw_per_cm2_per_nm, fill_value="extrapolate")
    new_wls = np.arange(380, 781, 1)
    uw_per_cm2_per_nm = f(new_wls)

    # old way used spectres
    # uw_per_cm2_per_nm = spectres.spectres(new_wls, spectra.columns.to_numpy(
    #         dtype='float'), uw_per_cm2_per_nm.to_numpy())

    uw_per_cm2_per_nm = np.where(uw_per_cm2_per_nm < 0, 0, uw_per_cm2_per_nm)
    w_per_m2_per_nm = pd.DataFrame(uw_per_cm2_per_nm * 0.01)
    w_per_m2_per_nm.columns = pd.Int64Index(new_wls)

    return w_per_m2_per_nm


# if __name__ == '__main__':
#     oo = OceanOptics.from_first_available()
#     try:
#         counts, _ = oo.measurement()
#     except KeyboardInterrupt:
#         print('Terminated by useer')
#     finally:
#         oo.close()
