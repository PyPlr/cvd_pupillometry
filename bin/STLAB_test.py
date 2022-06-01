#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 09:38:06 2022

@author: jtm545
"""

from time import sleep

from pyplr.stlab import SpectraTuneLab
from pyplr.stlabhelp import make_spectrum_s

d = SpectraTuneLab(
    password='23acd0c3e4c5c533', 
    default_address=1023, 
    lighthub_ip='192.168.6.2'
    )

d.demo(1)
d.demo(2)
d.set_colour_priority(False, 2)
