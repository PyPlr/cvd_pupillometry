#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 10:40:13 2022

@author: jtm

Make a video file describing a sinusoidal luminance modulation and play it
with STLAB.
"""

from time import sleep

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from pyplr.stlabscene import SpectraTuneLabScene
from pyplr.stlabhelp import make_spectrum_s, make_video_file
from pyplr.protocol import timer

d = SpectraTuneLabScene(
    password="23acd0c3e4c5c533", default_address=1023, lighthub_ip="192.168.6.2"
)


# Make video file
Fs = 100
sequence = np.linspace(0, 2 * np.pi, Fs)
x = (np.sin(sequence) + 1) / 2
cycle = (np.array([x for led in range(10)]) * 4096).round().astype("int")
t = np.linspace(0, 1000, 100).astype("int")
cycle = np.insert(cycle, 0, t, axis=0)
cycle = pd.DataFrame(cycle.T)
cycle.columns = [
    "time" if c == 0 else "LED-" + str(c - 1) for c in cycle.columns
]
metadata = {"title": "1Hz luminance modulation", "seconds": 20}
vf = make_video_file(cycle, repeats=20, fname="video1", **metadata)
vf = d.upload_video("video1.dsf")
d.set_spectrum_a([2048] * 10, 1023)
sleep(10)
timer(1, 10, "Waiting 10 s...")
d.scene(1021, 1022, "video1.dsf", "video1.dsf")
timer(1, 20, f'Playing video file: {vf["metadata"]["title"]}')
