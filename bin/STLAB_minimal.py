#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  4 10:41:33 2021

@author: jtm
"""
from time import sleep

from pyplr.stlab import SpectraTuneLab

d = SpectraTuneLab(password='23acd0c3e4c5c533', lighthub_ip='192.168.6.2')

for led in range(10):
    spec = [0]*10
    spec[led] = 4095
    d.set_spectrum_a(spec)
    sleep(1)
    d.turn_off()
    sleep(1)