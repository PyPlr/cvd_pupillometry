#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 09:38:06 2022

@author: jtm545

Minimal STLAB example. Set each channel to half power for 1 second.

"""

from time import sleep

from pyplr.stlab import SpectraTuneLab


# Maximum intensity setting for STLABs LED channels
MAXTENSITY = 4095


def main():
    try:
        # Authenticate with STLAB
        d = SpectraTuneLab.from_config()

        # Turn each channel on at half power for 1 s
        for led in range(10):
            spec = [0] * 10
            spec[led] = int(MAXTENSITY / 2)
            d.set_spectrum_a(spec)
            sleep(1)
            d.turn_off()
            sleep(1)

    except KeyboardInterrupt:
        print("> STLAB test terminated by user.")

    finally:
        d.turn_off()
        d.logout()
        print("> Logging out of STLAB.")


if __name__ == "__main__":
    main()
