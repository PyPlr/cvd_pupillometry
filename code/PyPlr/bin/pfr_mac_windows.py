#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep  7 13:06:12 2020

@author: jtm
"""
import sys
from time import time, sleep

import stlab
from pupil import new_trigger, PupilCore, LightStamper


# set up pupil
p = PupilCore()
p.command('T {}'.format(time()))

# setup stlab and generate a low-intensity 1s pulse of white light
if sys.platform == 'darwin':
    url = '192.168.6.2'
else:
    url = '192.168.7.2'
d = stlab.STLAB(username='admin', identity=1, password='83e47941d9e930f6', url=url)
d.load_video_file('1s_pulse.dsf')
spec = [100]*10 
stlab.make_video_pulse([100]*10, 1000, '1s_pulse')

# set up pupil trigger
label = 'LIGHT_ON'
trigger = new_trigger(label)
threshold = 15
wait_time = 6.

# start recording and wait 10 s
p.command('R pfr_mac_windows_tests')
sleep(10.)  

# 30 1s pulses
for i in range(30):
    # start LightStamper
    lst  = LightStamper(p, trigger, threshold, wait_time)
    lst.start()
    
    # wait 100 ms then present stimulus
    sleep(1.)
    d.play_video_file()
    
    sleep(10.)

# wait for 5 s and stop recording
sleep(5.)   
p.command('r')