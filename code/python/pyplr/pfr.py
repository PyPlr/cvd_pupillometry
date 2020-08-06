#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug  4 17:07:10 2020

@author: jtm
"""

'''
This script aims to do essentially what a neuroptics pupillometer does - 
adminster a light flash and give an instant read out of the data and PLR
parameters. Works well, but plenty of scope for optimising. 
'''

from time import time, sleep

import numpy as np
import pandas as pd

import stlab
from pupil import new_trigger, PupilCore, LightStamper, PupilGrabber
from pyplr import plr_metrics, plot_plr

# func to smooth the pupil data
def butterworth_series(samples,
                       filt_order=3,
                       cutoff_freq=.05,
                       inplace=False):
    '''
    Applies a butterworth filter to the given fields
    See documentation on scipy's butter method FMI.
    '''
    import scipy.signal as signal
    samps = samples if inplace else samples.copy(deep=True)
    B, A = signal.butter(filt_order, cutoff_freq, output='BA')
    samps = signal.filtfilt(B, A, samps)
    return pd.Series(samps)

# set up pupil
pupil = PupilCore()
pupil.command('T {}'.format(time()))

# setup stlab
stlab.make_video_pulse([250]*10, 1000, '1s_pulse')
d = stlab.STLAB(username='admin', identity=1, password='83e47941d9e930f6')
d.load_video_file('1s_pulse.dsf')

# set up trigger
label = 'LIGHT_ON'
trigger = new_trigger(label)
threshold = 15
wait_time = 5.

# start recording
pupil.command('R plr_integration_tests')

sleep(2.)  

# start LightStamper and PupilGrabber
lst = LightStamper(pupil, trigger, threshold, wait_time)
pgt = PupilGrabber(pupil, topic='pupil.1.3d', secs=10)
lst.start()
pgt.start()

# wait for a couple of seconds, then shine light
sleep(2.)
d.play_video_file()

# wait for 10 seconds and stop recording
sleep(10.)   
pupil.command('r')

# retrieve and process pupil data
di  = pd.Series(pgt.get('diameter_3d'))
di = butterworth_series(di, filt_order=3, cutoff_freq=.05)
ts = np.array(pgt.get('timestamp'))
conf = np.array(pgt.get('confidence'))
idx = (np.abs(ts - lst.timestamp)).argmin()
plr_metrics(di, 120, idx, 0.01)
plot_plr(di, 120, idx, 1, vel_acc=True, stamp_metrics=True)

