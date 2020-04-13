# -*- coding: utf-8 -*-
"""
Created on Wed Apr  8 15:25:58 2020

@author: engs2242
"""

import os
import pyplr as plr
import pandas as pd
import seaborn as sns

# useful strings
exp_dir = "..\\..\\..\\data\\red_vs_blue_2s_pulse_3trials_each"
subdirs = [f.path for f in os.scandir(exp_dir) if f.is_dir()]

# handle for processed data
store = exp_dir + "\\processed.h5"

# loop on subjects
combined = pd.DataFrame()
for subdir in subdirs:
    subject = subdir[-6:]
    ranges = pd.read_hdf(store, key=subject)
    ranges["subject"] = subject
    ranges.diameter_3d.plot()
    combined = combined.append(ranges)

# plot grand averages    
ax = sns.lineplot(x="onset", y="diameter_3dpc", hue='color', data=combined,
             n_boot=10, ci=95, palette=['red','blue'])
ax.set_xlabel('Time (s)')
ax.set_ylabel('Pupil Diameter (%-Change)')
ax.set_xticks(range(0, 8400, 600))
ax.set_xticklabels([str(xtl) for xtl in range(-5,65,5)])
ax.axhspan(-60,-62, color='k', alpha=.3)
ax.hlines((-60.5,-61,-61.5,-62), 600,840, color='k')
ax.hlines(0, 0, 7600, color='k', ls=':', lw=1)
ax.vlines(600, -62, 10, color='k', ls=':', lw=1)
sns.despine(offset=10, trim=True)

# some parameters
sample_rate = 120
duration = 7600
onset = 600
pc = .01

# grand averages
averages = combined.groupby(by=["color","onset"]).mean()

# some plr metrics
metrics = averages.groupby(by=["color"]).agg(
    B   = ("diameter_3d", lambda s: plr.baseline(s, onset)),
    L   = ("diameter_3d", lambda s: plr.latency_to_constriction(s, sample_rate, onset, pc)),
    PC  = ("diameter_3d", lambda s: plr.peak_constriction(s, onset)),
    MCA = ("diameter_3d", lambda s: plr.maximum_constriction_amplitude(s, onset)),
    MCT = ("diameter_3d", lambda s: plr.time_to_peak_constriction(s, sample_rate, onset)),
    CT  = ("diameter_3d", lambda s: plr.constriction_time(s, sample_rate, onset, pc)),
    MCV = ("diameter_3d", lambda s: plr.maximum_constriction_velocity(s, sample_rate))
    )
