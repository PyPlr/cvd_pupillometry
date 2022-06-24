#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 10:40:13 2022

@author: jtm

Sample the spectral output of STLAB with its internal spectrometer and
optionally also with an external OceanOptics spectrometer.
"""

from pyplr.stlabsampler import SpectraTuneLabSampler
from pyplr.oceanops import OceanOptics


# Whether to also obtain samples with an external OceanOptics spectrometer
USE_OCEAN_OPTICS = True


def main():
    try:
        # Connect to devices
        d = SpectraTuneLabSampler.from_config()
        if USE_OCEAN_OPTICS:
            oo = OceanOptics.from_first_available()
            d.external = oo

        # Specify LEDs and intensities to be sampled. In this case, each
        # channel at its maximum setting. For a more complete profiling,
        # uncomment the lines below. This will sample each channel accross the
        # range of intensities in steps of 65.
        leds = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        intensities = [4095 for led in leds]

        # leds = [0, 1, 2, 3, 4, 5, 6 ,7 ,8 , 9]
        # intensities = [i for i in range(0, 4096, 65)]

        # Sample
        d.sample(leds=leds,
                 intensities=intensities,
                 randomise=True)

        # Save results to csv in current working directory
        d.make_dfs(save_csv=True)

    except KeyboardInterrupt:
        print('> Sampling interrupted by user. No data were saved.')

    finally:
        if USE_OCEAN_OPTICS:
            oo.close()
            print('> Closed connection with OceanOptics spectrometer.')
        d.turn_off()
        d.logout()
        print('> Logging out of STLAB.')


if __name__ == '__main__':
    main()
