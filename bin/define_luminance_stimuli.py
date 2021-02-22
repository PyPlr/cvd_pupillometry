# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 12:17:54 2020

@author: engs2242
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import STLAB_apy as stlab
import seaborn as sns

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
duration = 10 # s

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
    stlab.make_video_file(df, fname)


time  = get_sinusoid_time_vector(duration)
sm = sinusoid_modulation(freq, duration, Fs)
amplitude2 = np.linspace(mintensity, maxtensity/2, len(time))
ivals = modulate_intensity_amplitude(sm, background, amplitude)

fig, ax = plt.subplots(figsize=(12,4))
plt.plot(time, ivals)



###

from scipy.signal import chirp
import matplotlib.pyplot as plt

sns.set_style('white')

duration=36
time  = get_sinusoid_time_vector(duration)
stim = np.zeros(duration*Fs)
stim[200:500]  = 4095
stim[800:1000] = 2048
sm = sinusoid_modulation(1.5, 10, Fs)
ivals = modulate_intensity_amplitude(sm, background, np.linspace(0,amplitude,10*Fs))

T = 10
n = 1000
t = np.linspace(0, T, n, endpoint=False)
f0 = 1
f1 = 5
y = chirp(t, f0, T, f1, method='linear', phi=270)
chp = modulate_intensity_amplitude(y, background, amplitude)
stim[1000:2000] = chp
stim[2000:2200] = background
stim[2200:3200] = ivals
stim[3200:3400] = background

fig, ax = plt.subplots(figsize=(12,4))
plt.plot(stim)
plt.ylim((0,15000))
sns.despine(fig)
ax.set_yticklabels([])
ax.set_yticks([])
ax.set_xticklabels([])
ax.set_xticks([])


df = pd.DataFrame()
cols = ["time"] + ["primary-" + str(x) for x in range(1,11)]
data = [stim for x in range(10)]
data.insert(0, time)
df = pd.DataFrame(data, cols).T
df = df.astype('int')
stlab.make_video_file(df, 'chirpo')





# import numpy as np
# from scipy.signal import chirp
# import matplotlib.pyplot as plt
# T = 10
# n = 1000
# t = np.linspace(0, T, n, endpoint=False)
# f0 = 1
# f1 = 10
# y = chirp(t, f0, T, f1, method='logarithmic', phi=270)
# #y += 2048
# plt.plot(t, y)
# plt.grid(alpha=0.25)
# plt.xlabel('t (seconds)')
# plt.show()

