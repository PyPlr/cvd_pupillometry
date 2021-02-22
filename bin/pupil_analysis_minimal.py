#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 19 19:57:46 2020

@author: jtm
"""

import pandas as pd

import pyplr.analysis as plr

# path to pupil labs recording directory
subjdir = ''

# some parameters
SAMPLE_RATE = 120

# pupil columns 
pupil_cols = ['diameter', 'diameter_3d']

# initialize subject analysis - assumes data is saved in 'subjdir/exports/000'
s = plr.init_subject_analysis(subjdir)

# load data - can use Pupil Labs blink detector or the Hershman algorithm
samples = plr.load_pupil(s['pl_data_dir'])
blinks  = plr.load_blinks(s['pl_data_dir'])

# interpolate zeros
samples = plr.interpolate_zeros(samples, fields=pupil_cols)

# interpolate blinks
samples = plr.interpolate_blinks(samples, blinks, fields=pupil_cols)

# smooth  
samples = plr.butterworth_series(samples, 
                                 fields=pupil_cols, 
                                 filt_order=3, 
                                 cutoff_freq=4/(SAMPLE_RATE/2))
