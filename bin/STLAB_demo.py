#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 11 09:04:46 2022

@author: jtm545
"""

from time import sleep
import random

from pyplr.stlab import SpectraTuneLab

d = SpectraTuneLab(
    password='23acd0c3e4c5c533', 
    default_address=1023, 
    lighthub_ip='192.168.6.2')

for led in range(10):
    spec = [0]*10
    spec[led] = 4095
    d.set_spectrum_a(spec)
    sleep(1)
    
d.turn_off()
sleep(1)

d.set_blink(30)
for s in range(100):
    spec = [random.randint(0, 4095) for led in range(10)]
    d.set_spectrum_a(spec)
d.set_blink(0)

d.turn_off()
