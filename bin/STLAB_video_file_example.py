#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  4 12:56:30 2020

@author: jtm

Make a video file describing a sinusoidal luminance modulation and play it
with STLAB.

"""

import numpy as np
import pandas as pd

from pyplr.stlab import SpectraTuneLab
from pyplr import stlabhelp
from pyplr.protocol import timer


# STLAB has a spectral switching time of 100 Hz, so we'll use this as our
# saplingfrequency
Fs = 100

# Maximum intensity setting for STLABs LED channels
MAXTENSITY = 4095


def main():
    try:
        # Create modulation profie in negative cosine phase.
        modulation_profile = np.linspace(0, 2 * np.pi, Fs)
        modulation_profile = (-np.cos(modulation_profile) + 1) / 2

        # Multiply modulation profile by MAXTENSITY and duplicate for each LED
        led_cycle = (
            (np.array([modulation_profile for led in range(10)]) * MAXTENSITY)
            .round()
            .astype("int")
        )

        # Create time vector and insert into array
        t = np.linspace(0, 1000, 100).astype("int")
        led_cycle = np.insert(led_cycle, 0, t, axis=0)

        # Make DataFrame and rename columns for maek_video_file function
        led_cycle = pd.DataFrame(led_cycle.T)
        led_cycle.columns = [
            "time" if c == 0 else "LED-" + str(c - 1) for c in led_cycle.columns
        ]

        # Add descriptive metadata and create video file. Note use of the
        # repeats value to play the modulation 10 times
        metadata = {"title": "1Hz luminance modulation", "seconds": 20}
        _ = stlabhelp.make_video_file(
            led_cycle, repeats=10, fname="video1", **metadata
        )

        # Authenticate with STLAB
        d = SpectraTuneLab.from_config()

        # Load the video file
        _ = d.load_video_file("video1.dsf")

        # Play
        d.play_video_file("video1.dsf")

        # Wait
        timer(1, 10, "> Playing video file...")

    except KeyboardInterrupt:
        print("> Demonstration terminated by user")

    finally:
        d.stop_video()
        d.turn_off()
        d.logout()
        print("> Logging out of STLAB.")


if __name__ == "__main__":
    main()
