#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 09:38:06 2022

@author: jtm545
"""

from time import sleep

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from pyplr.stlab import SpectraTuneLab
from pyplr.stlabhelp import make_spectrum_s, make_video_file
from pyplr.protocol import timer

d = SpectraTuneLab(
    password='23acd0c3e4c5c533', 
    default_address=1023, 
    lighthub_ip='192.168.6.2'
)

# Measure each channel
measurements = []
for led in range(10):
    spec = [0]*10
    spec[led] = 4095
    d.set_spectrum_a(spec)
    sleep(.5)
    _, m = d.get_spectrometer_spectrum(norm=False)
    measurements.append(m)
measurements = np.array(measurements)
for led, color in zip(measurements, d.colors):
    plt.plot(led, c=color)

# Get LED calibration
cal = d.get_led_calibration()
cal = np.array(cal)
for led, color in zip(cal, d.colors):
    plt.plot(led, c=color)


# Make a simple video file
Fs = 100
sequence = np.linspace(0, 2*np.pi, Fs)
x = (-np.cos(sequence) + 1) / 2
cycle = (np.array([x for led in range(10)]) * 4096).round().astype('int')
t = np.linspace(0, 1000, 100).astype('int')
cycle = np.insert(cycle, 0, t, axis=0)
cycle = pd.DataFrame(cycle.T)
cycle.columns = ['time' if c==0 else 'LED-' + str(c-1) for c in cycle.columns]
metadata = {'title': '1Hz luminance modulation', 'seconds': 20}
vf = make_video_file(cycle, repeats=20, fname='video1', **metadata)
vf = d.load_video_file('video1.dsf')
d.get_video_file_metadata('video1.dsf')
d.play_video_file('video1.json', address=1023)
duration = vf['metadata']['seconds']
name = vf['metadata']['title']
#timer(1, duration, name)
#d.turn_off()

