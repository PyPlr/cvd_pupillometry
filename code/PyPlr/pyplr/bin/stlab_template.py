#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 25 11:53:23 2020

@author: jtm
"""

from time import sleep
from pyplr import stlab

# set up device - strange how it doesn't seem to work first time
device = stlab.STLAB(username='admin', identity=1, password='83e47941d9e930f6')

# test spectrum
spectrum     = [0, 0, 0, 0, 0, 0, 0, 0, 0, 1000]
spectrum_off = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# 1 second light pulse
device.set_spectrum_a(spectrum)
sleep(1)
device.turn_off()