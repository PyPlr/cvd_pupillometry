# -*- coding: utf-8 -*-
"""
Created on Sat Mar 28 11:06:05 2020

@author: engs2242
"""

import pyplr as plr
import matplotlib.pyplot as plt

# recording directory
data_dir = "pipr_test/006/exports/000/"

# load data
samples = plr.load_pupil(data_dir)
events  = plr.load_annotations(data_dir)
blinks  = plr.load_blinks(data_dir)

# pupil columns
pupil_cols = ["diameter","diameter_3d"]

# interpolate blinks
samples = plr.interpolate_blinks(samples, blinks, interp_cols=pupil_cols)

# smooth - need to get right parameters
samples = plr.butterworth_series(samples, fields=pupil_cols, filt_order=3, cutoff_freq=.05, inplace=False)
samples = samples[pupil_cols]

# down sample - just take every other row for now, so 120 to 60 Hz
#samples = samples[::2]

# extract event ranges and baselines
events = events.query("label=='light_on'")
events.index = events["timestamp"]
ranges = plr.extract_events(samples, events, offset=-600, duration=7600,
                            borrow_attributes=["color"], return_count=False)
baselines = plr.extract_events(samples, events, offset=-600, duration=600,
                               borrow_attributes=["color"], return_count=False).mean(level=0)

# baseline normalise
ranges["diameter_pc"] = (ranges.diameter / baselines.diameter - 1).values * 100
ranges["diameter_3dpc"] = (ranges.diameter_3d / baselines.diameter_3d - 1).values * 100

# calculate averages for red and blue
ranges.reset_index(inplace=True)
averages = ranges.groupby(["color","onset"], as_index=True).mean()

# plot pipr
fig, ax = plt.subplots()
ax.plot(averages.loc["blue","diameter_3dpc"], color='blue')
ax.plot(averages.loc["red","diameter_3dpc"], color='red')
ax.set_xlabel('Time (s)')
ax.set_ylabel('Pupil Diameter (%-Change)')
ax.set_xticks(range(0, 8400, 600))
ax.set_xticklabels([str(xtl) for xtl in range(-5,65,5)])
ax.axhspan(-60,-62, color='k', alpha=.3)
ax.hlines((-60.5,-61,-61.5,-62), 600,840, color='k')
ax.hlines(0, 0, 7600, color='k', ls=':', lw=1)
ax.vlines(600, -62, 10, color='k', ls=':', lw=1)
fig.savefig(data_dir + 'pipr_plot.png')

# calculate metrics for averages
# B   = baseline (mm)
# L   = latency to constriction (ms)
# PC  = peak constriction (mm)
# MCA = maximum constriction amplitude (mm)
# MCT = maximum constriction time (ms)
# CT  = time of constriction (ms)
# MCV = maximum constriction velocity (mm/s)

# function parameters
sample_rate=120
onset_idx=600
pc=.01

# aggregate
metrics = averages.groupby(level=0).agg(
    B   = ("diameter_3d", lambda s: plr.baseline(s, onset_idx)),
    L   = ("diameter_3d", lambda s: plr.latency_to_constriction(s, sample_rate, onset_idx, pc)),
    PC  = ("diameter_3d", lambda s: plr.peak_constriction(s, onset_idx)),
    MCA = ("diameter_3d", lambda s: plr.maximum_constriction_amplitude(s, onset_idx)),
    MCT = ("diameter_3d", lambda s: plr.time_to_peak_constriction(s, sample_rate, onset_idx)),
    CT  = ("diameter_3d", lambda s: plr.constriction_time(s, sample_rate, onset_idx, pc)),
    MCV = ("diameter_3d", lambda s: plr.maximum_constriction_velocity(s, sample_rate))
    )

# save metrics
metrics.to_csv(data_dir + 'pipr_metrics.csv')
