# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 11:16:51 2020

@author: -
"""
import numpy as np
from time import sleep, time
import restful_apy as apy
import make_video_files as mvf
import matplotlib.pyplot as plt


# test spectrum
spectrum     = [1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000]
spectrum_off = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# make a video file from csv
mvf.make_video_file('led_test_sinusoid.csv', repeats=15)

# set up device - strange how it doesn't seem to work first time
device = apy.setup_device(username='admin', identity=1, password='83e47941d9e930f6')

# 1 second light pulse
apy.set_spectrum_a(device, spectrum)
sleep(1)
apy.turn_off(device)

# as above with 100 ms blink
apy.set_blink(device, 10)
apy.set_spectrum_a(device, spectrum)
sleep(1)
apy.set_blink(device, 0)
apy.turn_off(device)

# random disco
apy.random_disco(device, nlights=100, blink=20)

# load video file
apy.load_video_file(device, 'led_test_sinusoid.dsf')

# play video file and stop prematurely
apy.play_video_file(device)
sleep(3.)
apy.play_video_file(device, stop=True)

# turn off
apy.turn_off(device)

# turn light on and off 200 times and plot timing
t = []
for i in range(200):
    t1 = time()
    apy.spectruma(device, spectrum)
    sleep(.1)
    t2 = time()
    t.append(t2-t1)

    t3 = time()
    apy.spectruma(device, spectrum_off)
    sleep(.1)
    t4 = time()
    t.append(t4-t3)

plt.hist(t, bins=250)

# activate each primary, retrieve data from onboard spectrometer and plot
colors = ['blueviolet', 'royalblue', 'darkblue',
          'blue', 'cyan', 'green', 'lime', 
          'orange','red','darkred']
spectra = {}
for channel in range(10):
    intensity_values = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    intensity_values[channel] = 4095
    apy.set_spectrum_a(device, intensity_values)
    sleep(.2)
    spectra[channel] = apy.get_spectrometer_spectrum(device)
    sleep(.2)

spec_sum = np.zeros(81) 
for spectrum, color in zip(spectra, colors):
    bins = np.linspace(380,780,81)
    plt.plot(bins, np.array(spectra[spectrum][1:])*spectra[spectrum][0], color=color)
plt.plot(bins, spec_sum, color='k', ls=':')

# retrieve and plot led calibrations
matrix = apy.get_led_calibration(device)   
for calibration, color in zip(matrix, colors):
    bins = np.linspace(380,780,81)
    plt.plot(bins, calibration, color=color)    
    
# get temperature
temps = apy.get_pcb_temperature(device)

# turn off
apy.turn_off(device)

