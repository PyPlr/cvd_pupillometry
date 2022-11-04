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

    Optional support for concurrent samples with external spectrometer.

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
            Acquire concurrent samples with an external spectrometer.
            Must be a device class with `.sample(...)` method that returns
            `pd.Series` and `dict`. See `pyplr.oceanops.OceanOptics`
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

    def make_dfs(self) -> None:
        """Turn cached samples into DataFrames.

        Parameters
        ----------
        stlab_prefix : str
            Prefix for stlab data.
        external_prefix : str
            Prefix for external data.

        Returns
        -------
        None.

        """
        self.stlab_info = pd.DataFrame(self.stlab_info).set_index(
            ["Primary", "Setting"]
        )
        self.stlab_spectra = pd.DataFrame(self.stlab_spectra)
        self.stlab_spectra.columns = pd.Int64Index(self.wlbins)
        self.stlab_spectra.index = self.stlab_info.index

        if self.external is not None:
            self.ex_info = pd.DataFrame(self.ex_info).set_index(
                ["Primary", "Setting", "Measurement"]
            )
            self.ex_spectra = pd.DataFrame(self.ex_spectra)
            self.ex_spectra.columns = self.external.wavelengths()
            self.ex_spectra.index = self.ex_info.index

    def save_samples(self, stlab_prefix: str = "stlab", external_prefix: str = "external") -> None:
        self.stlab_spectra.to_csv(
            op.join(os.getcwd(), f"{stlab_prefix}_spectra.csv"), index=True
        )
        self.stlab_info.to_csv(
            op.join(os.getcwd(), f"{stlab_prefix}_info.csv"), index=True
        )
        if self.external is not None:
            self.ex_spectra.to_csv(
                op.join(os.getcwd(), f"{external_prefix}_spectra.csv"),
                index=True,
            )
            self.ex_info.to_csv(
                op.join(os.getcwd(), f"{external_prefix}_info.csv"),
                index=True,
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
        collect_dark_spectra: bool = False,
        **external_kwargs,
    ) -> None:
        """Sample a set of LEDs individually at a range of specified
        intensities using STLABs on-board spectrometer. Alternatively, sample
        a set of pre-defined spectra. Option to also obtain concurrent
        samples with an external Ocean Optics spectrometer. Data are
        stored in class lists.

        Parameters
        ----------
        leds : list
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
            a sample from the spectrometer(s). The default is .2.
        randomise : bool, optional
            Whether to randomise the order in which the LED-intensity settings
            or spectra are sampled. The default is False.
        collect_dark_spectra : bool
            If `True`, will collect a dark spectrum after each light spectrum
            using the same integration time. The default is `False`.


        Returns
        -------
        None.

        """
        if spectra and (leds or intensities):
            raise ValueError(
                "leds and intensities must be None when specifying spectra"
            )

        # Clear the cache
        self._ready_cache()

        # Off spectrum
        leds_off = [0] * 10

        # Turn stlab off if it's on
        self.set_spectrum_a(leds_off)

        # Generate the settings
        if spectra is not None:
            settings = spectra
            print(f"Sampling {len(spectra)} spectra: {spectra}")
        else:
            settings = [(l, i) for l in leds for i in intensities]
            print(
                "Sampling {len(leds)} primaries at the following settings: "
                + f"{intensities}\n"
            )

        # Shuffle
        if randomise:
            shuffle(settings)

        # Begin sampling
        for i, s in enumerate(settings):
            if not spectra:
                led, intensity = s[0], s[1]
                setting = {"Primary": led, "Setting": intensity}
                s = [0] * 10
                s[led] = intensity
                print(
                    f"Sample: {i+1} / {len(settings)}, Primary: {led}, "
                    + f"Setting: {intensity}"
                )
            else:
                setting = {"intensities": s}
                print(f"Sample: {i+1} / {len(settings)}, spectrum: {s}")

            # Set the spectrum
            self.set_spectrum_a(s)
            sleep(wait_before_sample)

            # Full readout from STLAB
            stlab_spec, stlab_info_dict = self.full_readout(setting=setting)
            self.stlab_spectra.append(stlab_spec)
            self.stlab_info.append(stlab_info_dict)

            # Readout with external, if using
            if self.external is not None:
                print("~~~ Light spectrum ~~~")
                setting.update({'Measurement': 'light'})
                ex_spec, ex_info_dict = self.external.sample(
                    sample_id=setting, **external_kwargs
                )
                self.ex_spectra.append(ex_spec)
                self.ex_info.append(ex_info_dict)

                # Turn off for dark counts
                if collect_dark_spectra:
                    print("~~~ Dark spectrum ~~~")
                    self.set_spectrum_a(leds_off)
                    sleep(.01)
                    setting.update({'Measurement': 'dark'})
                    ex_dark, ex_dark_info = self.external.sample(
                        integration_time=ex_info_dict['integration_time'],
                        sample_id=setting, **external_kwargs
                    )
                    self.ex_spectra.append(ex_dark)
                    self.ex_info.append(ex_dark_info)

            sleep(1)
            self.set_spectrum_a(leds_off)
            sleep(1)

        # Turn off
        self.turn_off()
