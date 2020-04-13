# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 12:17:54 2020

@author: engs2242
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import make_video_files as mvf

def get_sinusoid_time_vector(duration):
    time = np.arange(0,(duration*1000),10).astype("int")
    return time

def sinusoid_modulation(f, duration, Fs=100):
    x  = np.arange(duration * Fs)
    sm = np.sin(2 * np.pi * f * x / Fs)
    return sm

def modulate_intensity_amplitude(sm, background, amplitude):
    ivals = (background + (sm * amplitude)).astype("int")
    return ivals

# ledmotive params
Fs = 100 # constrained by system
mintensity = 0
maxtensity = 4095

# desired modulation frequencys, stimulus durations, sampling frequency
frequencies = [2, 1, 0.5, 0.1, 0.05]
duration = 60 # s

# modulate the full range of intensity around the mid point
background  = maxtensity/2
amplitude   = maxtensity/2
#amplitude = np.linspace(background, maxintensity/2, duration*100) # 'chirp' pattern

# make the stimuli
for freq in frequencies:
    # time vector for dsf file
    time  = get_sinusoid_time_vector(duration)
    
    # sinusoidal modulation for led channel
    sm = sinusoid_modulation(freq, duration, Fs)
    
    # get intensity values
    ivals = modulate_intensity_amplitude(sm, background, amplitude)
    
    # plot
    fig, ax = plt.subplots(figsize=(12,4))
    plt.plot(time, ivals)
    
    # make a csv
    cols = ["time"] + ["primary-" + str(x) for x in range(1,11)]
    data = [ivals for x in range(10)]
    data.insert(0, time)
    df = pd.DataFrame(data, cols).T
    df['time'] += 10000
    df.loc[0,'time'] = 0
    fname = "f"+str(freq)+"dur"+str(duration)+".csv"
    df.to_csv(fname, index=False)
    mvf.make_video_file(fname)


