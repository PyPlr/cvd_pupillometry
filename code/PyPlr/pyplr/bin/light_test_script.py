# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 11:16:51 2020

@author: -
"""
from time import sleep
from pyplr import stlab

# set up device - strange how it doesn't seem to work first time
device = stlab.SpectraTuneLab(username='admin', identity=1, password='2294b16eea08a15a')

# show colours in synchronous mode
for led in range(10):
    spectrum = [0]*10
    spectrum[led] = 4095
    
    # 1 second light pulse
    device.set_spectrum_a(spectrum)
    sleep(1)
    device.turn_off()

