#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 15 08:41:23 2021

@author: jtm
"""

import pandas as pd

from pyplr import plr

data = pd.read_csv('/Users/jtm/OneDrive - Nexus365/plr_protocol_1/ideal_plr.csv')

plr.plr_parameters(plr=data.diameter_3d, 
                   sample_rate=120,
                   onset_idx=600)

plr.plot_plr(plr=data.diameter_3d[0:1800], 
             sample_rate=120,
             onset_idx=600, 
             stim_dur=1,
             vel_acc=True,
             print_params=True)

vel = plr.velocity_profile(data.diameter_3d, 120)
acc = plr.acceleration_profile(data.diameter_3d, 120)
b = plr.pupil_size_at_onset(data.diameter_3d, onset_idx=600)
lidx = plr.latency_idx_a(data.diameter_3d, onset_idx=600)
lidx = plr.latency_idx_b(data.diameter_3d, onset_idx=600, sample_rate=120)
