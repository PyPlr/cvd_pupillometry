#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep  7 13:06:12 2020

@author: jtm
"""
import sys
from time import sleep

import stlab
from pupil import new_trigger, PupilCore, LightStamper


# set up pupil
p = PupilCore()
#p.command('T {}'.format(time())) # don't need this?

# setup stlab and generate a low-intensity 1s pulse of white light
if sys.platform == 'darwin':
    url = '192.168.7.2'
else:
    url = '192.168.7.2'
d = stlab.STLAB(username='admin', identity=1, password='83e47941d9e930f6', url=url)
spec = [0, 0, 0, 0, 0, 0, 4095, 4095, 0, 0]
stlab.make_video_pulse(spec, 1000, '1s_pulse')
d.load_video_file('1s_pulse.dsf')

# trigger params
threshold = 15
wait_time = 6.

# set up world trigger
world_label = 'LIGHT_ON_WORLD'
world_trigger = new_trigger(world_label)

# set up eye trigger
eye_label = 'LIGHT_ON_EYE'
eye_trigger = new_trigger(eye_label)

# start recording and wait 10 s
p.command('R pfr_mac_windows_tests')

# 30 1s pulses
for i in range(30):
    # start LightStamper
    lst_world = LightStamper(p, world_trigger, threshold, wait_time, subscription='frame.world')
    lst_eye_1 = LightStamper(p, eye_trigger, threshold, wait_time, subscription='frame.eye.1')

    lst_world.start()
    lst_eye_1.start()
    
    # wait 100 ms then present stimulus
    sleep(1.)
    d.play_video_file()
    
    sleep(4.)

# wait for 5 s and stop recording
sleep(5.)   
p.command('r')