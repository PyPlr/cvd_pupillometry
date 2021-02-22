#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  4 12:56:30 2020

@author: jtm
"""

from pyplr import stlab
import pandas as pd

df = stlab.pulse_protocol(pulse_spec=[0,0,0,400,0,0,0,0,0,0], 
                          pulse_duration=1000, 
                          fname='pulse', 
                          return_df=True,
                          metadata={'color':'blue'})
stlab.video_file_to_dict('pulse.dsf')

df = stlab.background_pulse_protocol(background_spec=[100]*10, 
                                     pre_pulse_duration=5000,
                                     pulse_spec=[0]*10, 
                                     pulse_duration=1000, 
                                     post_pulse_duration=5000, 
                                     fname='background_pulse', 
                                     return_df=True,
                                     metadata={'who':'me'})
stlab.video_file_to_dict('background_pulse.dsf')['metadata']

