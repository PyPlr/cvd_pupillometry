# -*- coding: utf-8 -*-
"""
Created on Wed Apr  8 15:25:58 2020

@author: engs2242
"""

import os
import pyplr as plr
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

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
    combined = combined.append(ranges)

combined.reset_index(inplace=True)

# plot grand averages    
fig, axs = plt.subplots(nrows=2, ncols=3, sharex=True, sharey=True, figsize=(14,8))
axs = [item for sublist in axs for item in sublist]
p = 0
for sub, df in combined.groupby('subject'):
    averages = df.groupby(by=["color","onset"], as_index=True).mean()

    axs[p].plot(averages.loc['red', "diameter_3dpc"], color='red')
    axs[p].plot(averages.loc['blue', "diameter_3dpc"], color='blue')
    axs[p].set_title(sub)
    p+=1
sns.lineplot(x="onset", y="diameter_3dpc", hue='color', data=combined,
             n_boot=10, ci=95, palette=['red','blue'], ax=axs[p], legend=False)

for ax in axs[3:]:
    ax.set_xlabel("Time (s)")
    
for ax in [axs[0], axs[3]]:
    ax.set_ylabel("Pupil modulation (%)")

for ax in axs:
    ax.set_xticks(range(600, 8400, 1200))
    ax.set_xticklabels([str(xtl) for xtl in range(0,65,10)])
    ax.axvspan(600,800,0,1,color='k', alpha=.2) 
    ax.hlines(0, 0, 7600, color='k', ls=':', lw=1.5)
    ax.set_ylim((-60,40))
axs[-1].set_title("Grand averages")
fig.savefig(exp_dir + "\\subject_and_grand_averages.png")
    
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
