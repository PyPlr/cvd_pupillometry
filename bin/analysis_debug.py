#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 22 09:38:00 2021

@author: jtm
"""
import numpy as np

from pyplr import utils
from pyplr import preproc
from pyplr import graphing

pupil_cols = ['diameter_3d', 'diameter']
SAMPLE_RATE=120
rec_dir = '/Users/jtm/OneDrive - Nexus365/protocols/pipr_protocol/JTM_b'
utils.print_file_structure(rec_dir)
s = utils.new_subject(rec_dir, export='000', out_dir_nm='pyplr_analysis')
samples = utils.load_pupil(s['data_dir'], eye_id='best')
events = utils.load_annotations(s['data_dir'])
blinks = utils.load_blinks(s['data_dir'])

# make figure for processing
f, axs = graphing.pupil_preprocessing(nrows=5, subject='test')

# plot the raw data
samples[pupil_cols].plot(title='Raw', ax=axs[0], legend=False)

# # masking
samples = preproc.mask_pupil_first_derivative(
    samples, threshold=3.0, mask_cols=pupil_cols)
samples[pupil_cols].plot(title='Masked 1st deriv (<SD*3)', ax=axs[1], legend=False)
samples = preproc.mask_pupil_confidence(
    samples, threshold=0.8, mask_cols=pupil_cols)
samples[pupil_cols].plot(title='Masked confidence (<0.8)', ax=axs[2], legend=False)

# interpolate blinks
samples = preproc.interpolate_pupil(samples, interp_cols=pupil_cols, method='linear', order=2)
samples[pupil_cols].plot(title='Linear interpolation', ax=axs[3], legend=False)

# smooth  
samples = preproc.butterworth_series(samples, 
                                  fields=pupil_cols, 
                                  filt_order=3, 
                                  cutoff_freq=4/(SAMPLE_RATE/2))
samples[pupil_cols].plot(title='Butterworth filtered', 
                         ax=axs[4], 
                         legend=False)

even = preproc.even_samples(samples, fields=pupil_cols, sample_rate=120)
even[pupil_cols].plot(ax=axs[4], legend=False, lw=.5)

DURATION = 7600
ONSET_IDX = 600

# extract the events and their baselines
ranges = utils.extract(samples, 
                 events, 
                 offset=-ONSET_IDX, 
                 duration=DURATION, 
                 borrow_attributes=['color'])
baselines = ranges.loc[(slice(None), slice(0,600)), :].mean(level=0)

# new columns for percent signal change
ranges = preproc.percent_signal_change(ranges, baselines, pupil_cols)


p = ranges.mean(level=1)

from pyplr import plr

params = plr.plr_parameters(p.diameter_3d, sample_rate=120, onset_idx=600, pc=.01)

# averaging takes care of things