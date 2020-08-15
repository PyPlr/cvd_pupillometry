# -*- coding: utf-8 -*-
"""
Created on Sat Mar 28 11:06:05 2020

@author: engs2242
"""

import os
import os.path as op
import pyplr as plr
import matplotlib.pyplot as plt
from pandas import HDFStore
from based_noise_blinks_detection import based_noise_blinks_detection

# directories for analysis
expdir = r"C:\Users\engs2242\Documents\repos\cvd_pupillometry\data\sinusoid_video_file"
subjdirs = [op.join(expdir,s) for s in os.listdir(expdir) if s.startswith("sub")]

# columns to load and analyse
load_cols =  ["pupil_timestamp","diameter","diameter_3d"]
pupil_cols = ["diameter","diameter_3d"]

# some parameters
sample_rate = 120
duration = 7600
onset = 600
pc = .01

# main analysis loop
for subjdir in subjdirs:
    # initialize subject analysis
    subjid, pl_data_dir, out_dir = plr.init_subject_analysis(subjdir, out_dir_nm="analysis")

    # load data - can use Pupil Labs blink detector or the Hershman algorithm
    samples = plr.load_pupil(pl_data_dir, cols=load_cols)
    events  = plr.load_annotations(pl_data_dir)
    #blinks  = plr.load_blinks(pl_data_dir)
    blinks = based_noise_blinks_detection(samples["diameter"], sample_rate)
    
    # plot the raw data
    ax = samples[pupil_cols].plot(figsize=(14,4), title=subjid+": raw")
    ax.get_figure().savefig(out_dir + "\\raw.png")
    
    # interpolate zeros, then blinks, then smooth
    samples = plr.interpolate_zeros(samples, fields=pupil_cols)
    ax = samples[pupil_cols].plot(figsize=(14,4), title=subjid+": zeros interpolated")
    ax.get_figure().savefig(out_dir + "\\zeros interpolated.png")
    samples = plr.interpolate_blinks(samples, blinks, fields=pupil_cols)
    ax = samples[pupil_cols].plot(figsize=(14,4), title=subjid+": blinks interpolated")
    ax.get_figure().savefig(out_dir + "\\blinks interpolated.png")
    samples = plr.savgol_series(samples, fields=pupil_cols, window_length=51, filt_order=7)
    #samples = plr.butterworth_series(samples, fields=pupil_cols, filt_order=3, cutoff_freq=.05)
    ax = samples[pupil_cols].plot(figsize=(14,4), title=subjid+": butterworth filtered")
    ax.get_figure().savefig(out_dir + "\\butterworth filtered.png")
    
    # get the events of interest
    events = events.query("label=='video_start'")
    events.index = events["timestamp"]
    
    # extract the events and their baselines
    ranges = plr.extract(samples, events, offset=-onset, duration=duration, 
                         borrow_attributes=["stim"])
    baselines = plr.extract(samples, events, offset=-onset, duration=onset,
                            borrow_attributes=["stim"]).mean(level=0)
    
    # new columns for baseline normalised data
    ranges["diameter_pc"] = (ranges.diameter / baselines.diameter - 1).values * 100
    ranges["diameter_3dpc"] = (ranges.diameter_3d / baselines.diameter_3d - 1).values * 100

    # drop / markup bad trials
    ranges = plr.reject_bad_trials(ranges, interp_thresh=20, drop=True)
    
    # calculate averages for conditions
    averages = ranges.reset_index().groupby(by=["stim","onset"], as_index=True).mean()

    # plot pipr
    fig, ax = plt.subplots()
    ax.plot(averages.loc['f1dur60.dsf', "diameter_3dpc"], color='red')
    ax.plot(averages.loc['f0.5dur60.dsf', "diameter_3dpc"], color='blue')
    ax.plot(averages.loc['f0.05dur60.dsf', "diameter_3dpc"], color='blue')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Pupil Diameter (%-Change)')
    ax.set_xticks(range(0, 8400, 600))
    ax.set_xticklabels([str(xtl) for xtl in range(-5,65,5)])
    ax.axhspan(-60,-62, color='k', alpha=.3)
#    ax.hlines((-60.5,-61,-61.5,-62), 600,840, color='k')
    ax.hlines(0, 0, 7600, color='k', ls=':', lw=1)
    ax.vlines(600, -62, 10, color='k', ls=':', lw=1)
    fig.savefig(out_dir + '\\sinusoid_plot.png')
    
    # calculate metrics for averages
    # B   = baseline (mm)
    # L   = latency to constriction (ms)
    # PC  = peak constriction (mm)
    # MCA = maximum constriction amplitude (mm)
    # MCT = maximum constriction time (ms)
    # CT  = time of constriction (ms)
    # MCV = maximum constriction velocity (mm/s)
    
    # aggregate
    metrics = averages.groupby(level=0).agg(
        B   = ("diameter_3d", lambda s: plr.baseline(s, onset)),
        L   = ("diameter_3d", lambda s: plr.latency_to_constriction(s, sample_rate, onset, pc)),
        PC  = ("diameter_3d", lambda s: plr.peak_constriction(s, onset)),
        MCA = ("diameter_3d", lambda s: plr.maximum_constriction_amplitude(s, onset)),
        MCT = ("diameter_3d", lambda s: plr.time_to_peak_constriction(s, sample_rate, onset)),
        CT  = ("diameter_3d", lambda s: plr.constriction_time(s, sample_rate, onset, pc)),
        MCV = ("diameter_3d", lambda s: plr.maximum_constriction_velocity(s, sample_rate))
        )
    
    # save metrics
    metrics.to_csv(out_dir + '\\pipr_metrics.csv')
    
    # add the subject id
    ranges["subjid"] = subjid
    
    # append processed data to HDFStore
    processed = HDFStore(expdir + '\\processed.h5')
    processed.put(subjid, ranges, format="table")
    processed.close()
    
