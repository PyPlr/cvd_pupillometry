#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 11:28:17 2022

@author: jtm

Module with stlab.SpectraTuneLab subclass designed for sampling spectral data
with the internal spectrometer, and optionally, and external spectrometer.

"""

import os
import os.path as op
from time import sleep
from random import shuffle
from typing import Tuple, List

import numpy as np
import pandas as pd

from pyplr.stlab import SpectraTuneLab


class SpectraTuneLabSampler(SpectraTuneLab):
    """Subclass of `stlab.SpectraTuneLab` with added sampling methods.

    Optional support for concurrent measurements with external spectrometer.

    """

    def __init__(
        self,
        password: str,
        username: str = "admin",
        default_address: int = 1023,
        lighthub_ip: str = "192.168.7.2",
        external: object = None,
    ) -> None:
        """Initialize class and subclass. See `pyplr.stlab.SpectraTuneLab` for
        more info.

        Parameters
        ----------
        external : Class, optional
            Acquire concurrent measurements with an external spectrometer.
            Must be a device class with ``.measurement(...)`` and
            ``.wavelengths(...)`` methods. See `pyplr.oceanops.OceanOptics`
            for an example.

        Returns
        -------
        None.

        """

        super().__init__(password, username, default_address, lighthub_ip)
        self.external = external
        self._ready_cache()

    def _ready_cache(self):
        self.stlab_spectra = []
        self.stlab_info = []
        if self.external is not None:
            self.ex_spectra = []
            self.ex_info = []

    def make_dfs(
        self, save_csv: bool = False, external_fname: str = None
    ) -> None:
        """Turn cached data and info into pandas DataFrames.

        Parameters
        ----------
        save_csv : bool
            Optionally save to csv format in the current working directory.
        external_fname : str
            Prefix for filenames containing data from external spectrometer.

        Returns
        -------
        None.

        """
        if external_fname is None:
            external_fname = "external"

        self.stlab_spectra = pd.DataFrame(self.stlab_spectra)
        self.stlab_spectra.columns = pd.Int64Index(self.wlbins)
        self.stlab_info = pd.DataFrame(self.stlab_info)
        if "Primary" in self.stlab_info.columns:
            self.stlab_spectra["Primary"] = self.stlab_info["Primary"]
            self.stlab_spectra["Setting"] = self.stlab_info["Setting"]

        if self.external is not None:
            self.ex_spectra = pd.DataFrame(self.ex_spectra)
            self.ex_spectra.columns = self.external.wavelengths()
            self.ex_info = pd.DataFrame(self.ex_info)
            if "Primary" in self.ex_info.columns:
                self.ex_spectra["Primary"] = self.ex_info["Primary"]
                self.ex_spectra["Setting"] = self.ex_info["Setting"]

        if save_csv:
            self.stlab_spectra.to_csv(
                op.join(os.getcwd(), "stlab_spectra.csv"), index=False
            )
            self.stlab_info.to_csv(
                op.join(os.getcwd(), "stlab_info.csv"), index=False
            )
            if self.external is not None:
                self.ex_spectra.to_csv(
                    op.join(os.getcwd(), f"{external_fname}_spectra.csv"),
                    index=False,
                )
                self.ex_info.to_csv(
                    op.join(os.getcwd(), f"{external_fname}_info.csv"),
                    index=False,
                )

    def full_readout(
        self, norm: bool = False, setting: dict = {}
    ) -> Tuple[np.array, dict]:
        """Get a full readout from STLAB.

        Parameters
        ----------
        norm : bool
            Whether to normalise the spectrum to the peak radiometric value.
        setting : dict, optional
            The current setting of the luminaire (if known), to be included in
            the `info_dict`. For example ``{'led' : 5, 'intensity' : 3000}``,
            or ``{'intensities' : [0, 0, 0, 300, 4000, 200, 0, 0, 0, 0]}``.
            The default is ``{}``.

        Returns
        -------
        spec : np.array
            The spectrum.
        info_dict : dict
            Dictionary of information for spectrometer reading.

        """
        tmps = self.get_pcb_temperature()
        ip = self.get_input_power()
        it = self.get_spectrometer_integration_time()
        dl = self.get_dimming_level()
        rmv, spec = self.get_spectrometer_spectrum(norm=norm)
        info_dict = {
            "rmv": rmv,
            "LEDs_temp": tmps[0],
            "drivers_temp": tmps[1],
            "board_temp": tmps[2],
            "micro_temp": tmps[3],
            "integration_time": it,
            "input_power": ip,
            "dimming_level": dl,
        }
        info_dict = {**info_dict, **setting}
        return (spec, info_dict)

    def sample(
        self,
        leds: List = [0],
        intensities: List = [500],
        spectra: List = None,
        wait_before_sample: float = 0.3,
        randomise: bool = False,
        **external_kwargs,
    ) -> None:
        """Sample a set of LEDs individually at a range of specified
        intensities using STLABs on-board spectrometer. Alternatively, sample
        a set of pre-defined spectra. Option to also obtain concurrent
        measurements with an external Ocean Optics spectrometer. Data are
        stored in class lists.

        Parameters
        ----------
        leds : list, optional
            List of unique integers from 0-9 representing the LEDs to sample.
            The default is [0].
        intensities : list, optional
            List of integer values between 0-4095 representing the intensity
            values at which to sample the LEDs. The default is [500].
        spectra : list, optinal
            List of predfined spectra to sample. Must be None if specifying
            leds or intensities. The default is None.
        wait_before_sample : float, optional
            Time in seconds to wait after setting a spectrum before acquiring
            a measurement from the spectrometer(s). The default is .2.
        randomise : bool, optional
            Whether to randomise the order in which the LED-intensity settings
            or spectra are sampled. The default is False.


        Returns
        -------
        None.

        """
        if spectra and (leds or intensities):
            raise ValueError(
                "leds and intensities must be None when specifying spectra"
            )

        # clear the cache
        self._ready_cache()

        # off spectrum
        leds_off = [0] * 10

        # turn stlab off if it's on
        self.set_spectrum_a(leds_off)

        # generate the settings
        if spectra:
            settings = spectra
            print("Sampling {} spectra: {}".format(len(spectra), spectra))
        else:
            settings = [(l, i) for l in leds for i in intensities]
            print(
                "Sampling {} primaries at the following settings: {}".format(
                    len(leds), intensities
                )
            )

        # shuffle
        if randomise:
            shuffle(settings)

        # begin sampling
        for i, s in enumerate(settings):
            if not spectra:
                led, intensity = s[0], s[1]
                setting = {"Primary": led, "Setting": intensity}
                s = [0] * 10
                s[led] = intensity
                print(
                    "Measurement: {} / {}, Primary: {}, Setting: {}".format(
                        i + 1, len(settings), led, intensity
                    )
                )
            else:
                setting = {"intensities": s}
                print(
                    "Measurement: {} / {}, spectrum: {}".format(
                        i + 1, len(settings), s
                    )
                )

            # set the spectrum
            self.set_spectrum_a(s)
            sleep(wait_before_sample)

            # full readout from STLAB
            stlab_spec, stlab_info_dict = self.full_readout(setting=setting)
            self.stlab_spectra.append(stlab_spec)
            self.stlab_info.append(stlab_info_dict)

            if self.external is not None:
                ex_spec, ex_info_dict = self.external.measurement(
                    setting=setting, **external_kwargs
                )
                self.ex_spectra.append(ex_spec)
                self.ex_info.append(ex_info_dict)

            sleep(1)
            self.set_spectrum_a(leds_off)
            sleep(1)

        # turn off
        self.turn_off()
