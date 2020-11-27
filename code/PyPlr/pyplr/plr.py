#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 15:08:28 2020

@author: jtm

A module to assist with parametrising and plotting pupillary light reflexes.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def velocity_profile(s, sample_rate):
    '''
    Return the velocity profile of a PLR.

    '''
    # TODO: This assumes the samples are evenly spaced, which is not the 
    # case with Pupil Labs. The correct calculation may be 
    # d.diameter_3d.diff() / d.orig_idx.diff()
    t = 1 / sample_rate
    return np.diff(s) / t

def acceleration_profile(s, sample_rate):
    '''
    Return the acceleration profile of a PLR.

    '''
    # TODO: This assumes the samples are evenly spaced, which is not the 
    # case with Pupil Labs. The correct calculation may be 
    # d.diameter_3d.diff() / d.orig_idx.diff()
    t = 1 / sample_rate
    vel = velocity_profile(s, sample_rate)
    return np.diff(vel) / t

def baseline(s, onset_idx):
    '''
    Return the average pupil size between the start of s and onset_idx
    
    '''
    return np.mean(s[0:onset_idx])

def latency_idx(s, sample_rate, onset_idx, pc=None):
    '''
    Return the index of the first sample following stimulus onset where 
    constriction exceeds a percentage of the baseline. pc should be int or
    float for data already expressed as pc (e.g. pc=1 == pc=.01). 
    
    FIGURE OUT A BETTER WAY OF DOING THIS.    
    '''
    if pc is None:
        raise ValueError('Must specify int or float for pc')
    b = baseline(s, onset_idx)
    if isinstance(pc, float):
        threshold = b - (b * pc)
        lidx = np.argmax(s[onset_idx:] < threshold)
    elif isinstance(pc, int):
        threshold = b - pc
        lidx = np.argmax(s[onset_idx:] < threshold)
    lidx += onset_idx
    return lidx

def latency_to_constriction_a(s, sample_rate, onset_idx, pc=None):
    '''
    Return the time in miliseconds between stimulus onset and the first 
    sample where constriction exceeds a percentage of the baseline.
    
    '''
    lidx = latency_idx(s, sample_rate, onset_idx, pc=pc)
    return (lidx - onset_idx) * (1000 / sample_rate)

def latency_to_constriction_b(s, sample_rate, onset_idx):
    '''
    Return the time in miliseconds between stimulus onset and the time 
    at which the pupil reaches maximal negative acceleration within a 
    1-s window. See Bergamin & Kardon (2003) for justification. Requires 
    well-smoothed pupil data. 
    
    '''
    acc = acceleration_profile(s, sample_rate)
    return np.argmin(acc[onset_idx:onset_idx + sample_rate]) * (1000 / sample_rate)
    
def time_to_max_constriction(s, sample_rate, onset_idx):
    '''
    Return the time in miliseconds between stimulus onset and the peak 
    of pupil constriction.
    
    '''
    return np.argmin(s[onset_idx:]) * (1000 / sample_rate)


def time_to_max_velocity(s, sample_rate, onset_idx):
    '''
    Return the time between stimulus onset and when pupil constriction reaches 
    maximum velocity.
    
    '''
    vel = velocity_profile(s, sample_rate)
    return np.argmin(vel[onset_idx:]) * (1000 / sample_rate)

def peak_constriction_idx(s):
    '''
    Return the index of the sample with peak constriction.
    
    '''
    return np.argmin(s)

def peak_constriction(s):
    '''
    Return the peak constriction value (i.e. the smallest pupil size).
    
    '''
    return np.min(s)

def constriction_amplitude(s, onset_idx):
    '''
    Return the constriction amplitude (i.e. the absolute difference 
    between baseline and peak constriction).
    
    '''
    peak = peak_constriction(s)
    base = baseline(s, onset_idx)
    return abs(peak - base)

def average_constriction_velocity(s, sample_rate, onset_idx, pc):
    '''
    Return the average constriction velocity.

    '''
    vel  = velocity_profile(s, sample_rate)
    lidx = latency_idx(s, sample_rate, onset_idx, pc)
    pidx = peak_constriction_idx(s)
    return np.mean(abs(vel[lidx:pidx]))
    
def max_constriction_velocity(s, sample_rate, onset_idx):
    '''
    Return the maximum constriction velocity.
    
    '''
    vel  = velocity_profile(s, sample_rate)
    pidx = peak_constriction_idx(s)
    return np.max(abs(vel[onset_idx:pidx]))

def max_constriction_acceleration(s, sample_rate, onset_idx):
    '''
    Return the maximum constriction acceleration.
    
    '''
    acc  = acceleration_profile(s, sample_rate)
    pidx = peak_constriction_idx(s)
    return np.max(abs(acc[onset_idx:pidx]))

def constriction_time(s, sample_rate, onset_idx, pc=None):
    '''
    Return the time difference between constriction latency and peak constriction.
    
    '''
    lat  = latency_to_constriction_a(s, sample_rate, onset_idx, pc)
    ttmc = time_to_max_constriction(s, sample_rate, onset_idx)
    return  ttmc - lat

def max_redilation_velocity(s, sample_rate):
    '''
    Return the maximum redilation velocity.
    
    '''
    vel  = velocity_profile(s, sample_rate)
    pidx = peak_constriction_idx(s)
    return np.max(abs(vel[pidx:])) 

def max_redilation_acceleration(s, sample_rate):
    '''
    Return the maximum redilation acceleration.
    
    '''   
    acc  = acceleration_profile(s, sample_rate)
    pidx = peak_constriction_idx(s)
    return np.max(abs(acc[pidx:]))

def recovery_time_75pc(s, sample_rate, onset_idx):
    '''
    Return the time in ms until 75% recovery from baseline.
    
    '''
    base = baseline(s, onset_idx)
    pidx = peak_constriction_idx(s)
    amp  = constriction_amplitude(s, onset_idx)
    return np.argmax(s[pidx:] > base - (amp / 4)) * (1000 / sample_rate)

def plr_parameters(s, sample_rate, onset_idx, pc):
    '''
    Collapse a PLR into descriptive parameters.
    
    Parameters
    ----------
    s : array-like
        data representing a pupil's response to light.
    sample_rate : int
        sampling rate of the measurement system.
    onset_idx : int
        index of the onset of the light stimulus.
    pc : int, float
        the percentage of constriction from baseline to use in calculating
        constriction latency. Use float (e.g. pc=0.01) or int (e.g. pc=1)
        for data already expressed as %-modulation from baseline.
        
    Returns
    -------
    params : pd.DataFrame
        DataFrame containins the params.
    '''
    
    params = {
        'D1'       : baseline(s, onset_idx),
        'T1a'      : latency_to_constriction_a(s, sample_rate, onset_idx, pc),
        'T1b'      : latency_to_constriction_b(s, sample_rate, onset_idx),
        'T2'       : time_to_max_velocity(s, sample_rate, onset_idx),
        'T3'       : time_to_max_constriction(s, sample_rate, onset_idx),
        'T4'       : recovery_time_75pc(s, sample_rate, onset_idx),
        'D2'       : peak_constriction(s),
        'AMP'      : constriction_amplitude(s, onset_idx),
        'VelConMax': max_constriction_velocity(s, sample_rate, onset_idx),
        'VelConAve': average_constriction_velocity(s, sample_rate, onset_idx, pc),
        'AccConMax': max_constriction_acceleration(s, sample_rate, onset_idx),
        'CT'       : constriction_time(s, sample_rate, onset_idx, pc),
        'VelRedMax': max_redilation_velocity(s, sample_rate),
        'AccRedMax': max_redilation_acceleration(s, sample_rate)
        }
    params = pd.DataFrame.from_dict(params, orient='index')
    return params

def plot_plr(s, 
             sample_rate,
             onset_idx, 
             stim_dur,
             vel_acc=False,
             stamp_params=False):
    '''
    Plot a PLR with option to add descriptive parameters and 
    velocity / acceleration profiles. Useful for exploratory analysis.
    
    Parameters
    ----------
    s : pd.Series
        data representing a pupil's response to light.
    sample_rate : int
        sampling rate of the measurement system.
    onset_idx : int
        index of the onset of the light stimulus.
    stim_dur : float
        Duration (s) of the light stimulus.
    vel_acc : bool, optional
        Whether to also plot the velocity and acceleration profiles.
        The default is False.
    stamp_metrics : bool, optional
        Whether to annotate the axis with the results of a call to 
        plr_metrics(...). The default is False.
        
    Returns
    -------
    fig : matplotlib.figure.Figure
        the plot.
        
    '''
    #sns.set_context('poster', font_scale=1.2)
    b = baseline(s, onset_idx)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(s, lw=3)
    ax.axhline(b, 0, 1, ls='dashed', color='k', lw=1)
    ax.axvspan(onset_idx, onset_idx + (sample_rate * stim_dur), color='k', alpha=.3)
    ax.set_ylabel('Pupil Size')
    ax.set_xlabel('Time (s)')
    x  = [val for val in range(0, len(s) + (sample_rate * 2), sample_rate * 5)]
    xl = [str(val) for val in range(-int(onset_idx / sample_rate), int(len(s) / sample_rate), 5)]
    ax.set_xticks(x)
    ax.set_xticklabels(xl)
    
    if vel_acc:
        ax2 = ax.twinx()
        vel = velocity_profile(s, sample_rate)
        acc = acceleration_profile(s, sample_rate)
        ax2.plot(vel, color='g', lw=2)
        ax2.plot(acc, color='r', lw=1)
        ax2.set_ylabel('Velocity / Acceleration')
    
    if stamp_params:
        m = plr_parameters(s, sample_rate, onset_idx, pc=.01)
        m = m.round(3)
        ax.text(.78, .03, m.to_string(), size=8, transform=ax.transAxes)
            
    return fig

##########################################
# FUNCTIONS FOR CALCULATING PIPR METRICS #
##########################################

def pipr_amplitude(s, sample_rate, window):
    return s[window[0]:window[1]].mean()
 
def pipr_duration(s, sample_rate, onset_idx, duration):
    '''
    Return the time to return to baseline after light offset. ISI should be 
    between 100 and 660 s to allow pupil to return to baseline (see Adhikari
    et al., 2015)
    '''
    offset_idx = onset_idx + duration
    base = baseline(s, onset_idx)
    return np.argmax(s[offset_idx:] >= base) * (1000 / sample_rate)

def pipr_AUC_early(s, sample_rate, onset_idx, duration):
    '''
    Unitless - AUC between offset and 10 s post offset
    '''
    base = baseline(s, onset_idx)
    offset_idx = onset_idx + duration
    auc_idx = offset_idx + (sample_rate * 10)
    return np.sum(base - abs(s[offset_idx:auc_idx]))

def pipr_AUC_late(s, sample_rate, onset_idx, duration):
    '''
    Unitless - AUC between 10-30 s post offset
    '''
    base = baseline(s, onset_idx)
    offset_idx = onset_idx + duration
    auc_idx = offset_idx + (sample_rate * 10)
    return np.sum(base - abs(s[auc_idx:auc_idx + (sample_rate * 30)]))
    
# def pipr_parameters(s, sample_rate, onset_idx, pc):
#     '''
#     Collapse a PIPR into descriptive parameters.
    
#     Parameters
#     ----------
#     s : array-like
#         data representing a pupil's response to light.
#     sample_rate : int
#         sampling rate of the measurement system.
#     onset_idx : int
#         index of the onset of the light stimulus.
#     pc : int, float
#         the percentage of constriction from baseline to use in calculating
#         constriction latency. Use float (e.g. pc=0.01) or int (e.g. pc=1)
#         for data already expressed as %-modulation from baseline.
        
#     Returns
#     -------
#     params : pd.DataFrame
#         DataFrame containins the params.
#     '''
    
#     params = {

#         }
#     params = pd.DataFrame.from_dict(params, orient='index')
#     return params


# def plot_trials(ranges, sample_rate, onset_idx, stim_dur, pupil_col='diameter', out_dir=None):
#     if not isinstance(ranges.index, pd.MultiIndex):
#         ranges.set_index(['event','onset'], inplace=True)
#     for event, df in ranges.groupby(level=0):
#         f = plot_plr(df[pupil_col].values, sample_rate, onset_idx, stim_dur, vel_acc=True, stamp_metrics=True)
#         if out_dir:
#             f.savefig(out_dir + '\\event' + str(event) + '.png')