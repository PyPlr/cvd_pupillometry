#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 21 11:11:44 2020

@author: jtm
"""

#######################################################################
# THIS SCRIPT WAS TESTED WITH THE FOLLOWING SETTINGS IN PUPIL CAPTURE #
# 1. Resolution (320, 240) for eye and world                          #  
# 2. Frame rate 120 for eye and world                                 #
# 3. Auto Exposure mode - Manual Exposure - both cameras              # 
# 4. Absolute exposure time 60 for world, 63 for eye                  #
# 5. Frame publisher format - BGR                                     #
# 6. Dim lighting                                                     #
# 7. Annotation plugin enabled                                        #
#######################################################################

from time import time, sleep

from pupil import PupilCore, LightStamper, new_trigger

# set up pupil
p = PupilCore()
p.command('T {}'.format(time()))

# make trigger
label = 'LIGHT_ON'
trigger = new_trigger(label)
threshold = 15
wait_time = 10.

# start recording
p.command('R plr_integration_tests')
sleep(.2)

# start lightstamper
lst  = LightStamper(p, trigger, threshold, wait_time)
lst.start()
sleep(10)

# end recording
p.command('r')