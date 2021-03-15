#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
pyplr.plr
=========

A module to assist with parametrising and plotting pupillary light responses.

@author: jtm

'''

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt



def velocity_profile(plr, sample_rate):
    '''Return the velocity profile of a PLR. Assumes the samples are 
    evenly spaced, which is not the case with Pupil Labs data. Smoothing
    and averaging across multiple PLRs should remove cause for concern. 

    '''
    t = 1 / sample_rate
    return np.diff(plr, prepend=np.nan) / t

def acceleration_profile(plr, sample_rate):
    '''Return the acceleration profile of a PLR. Assumes the samples are 
    evenly spaced, which is not the case with Pupil Labs data. Smoothing
    and averaging across multiple PLRs should remove cause for concern. 

    '''
    t = 1 / sample_rate
    vel = velocity_profile(plr, sample_rate)
    return np.diff(vel, prepend=np.nan) / t

def baseline(plr, onset_idx):
    '''Return the average pupil size between the start of s and onset_idx.
    
    '''
    return np.mean(plr[0:onset_idx])

def pupil_size_at_onset(plr, onset_idx):
    '''Return pupil size at stimulus onset.

    '''
    return plr[onset_idx]

def latency_idx_a(plr, onset_idx):
    '''Return the index where pupil size passes 1% change from size at light
    onset.
    
    '''
    b = pupil_size_at_onset(plr, onset_idx)
    threshold = b - (b * .01)
    lidx = np.argmax(plr[onset_idx:] < threshold)
    lidx += onset_idx
    return lidx

def latency_idx_b(plr, sample_rate, onset_idx):
    '''Return the index of peak negative acceleration in the second after
    light onset.

    '''
    acc = acceleration_profile(plr, sample_rate)
    lidx = np.argmin(acc[onset_idx:onset_idx + sample_rate])
    lidx += onset_idx
    return lidx

    

def latency_to_constriction_a(plr, sample_rate, onset_idx):
    '''Return the time in miliseconds between stimulus onset and the first 
    sample where constriction exceeds a percentage of the baseline, using the
    percent change threshold.
    
    '''
    lidx = latency_idx_a(plr, onset_idx)
    return (lidx - onset_idx) * (1000 / sample_rate)

def latency_to_constriction_b(plr, sample_rate, onset_idx):
    '''Return the time in miliseconds between stimulus onset and the time 
    at which the pupil reaches maximal negative acceleration within a 
    1-s window. See Bergamin & Kardon (2003) for justification. Requires 
    well-smoothed pupil data. 
    
    '''
    lidx = latency_idx_b(plr, sample_rate, onset_idx)
    return (lidx - onset_idx) * (1000 / sample_rate)
    
def time_to_max_constriction(plr, sample_rate, onset_idx):
    '''Return the time in miliseconds between stimulus onset and the peak 
    of pupil constriction.
    
    '''
    return np.argmin(plr[onset_idx:]) * (1000 / sample_rate)


def time_to_max_velocity(plr, sample_rate, onset_idx):
    '''Return the time between stimulus onset and when pupil constriction reaches 
    maximum velocity.
    
    '''
    vel = velocity_profile(plr, sample_rate)
    return np.argmin(vel[onset_idx:]) * (1000 / sample_rate)

def peak_constriction_idx(plr):
    '''Return the index of the sample with peak constriction.
    
    '''
    return np.argmin(plr)

def peak_constriction(plr):
    '''Return the peak constriction value (i.e., the smallest pupil size).
    
    '''
    return np.min(plr)

def constriction_amplitude(plr, onset_idx):
    '''Return the constriction amplitude (i.e. the absolute difference 
    between baseline and peak constriction).
    
    '''
    peak = peak_constriction(plr)
    base = baseline(plr, onset_idx)
    return abs(peak - base)

def average_constriction_velocity(plr, sample_rate, onset_idx):
    '''Return the average constriction velocity.

    '''
    vel  = velocity_profile(plr, sample_rate)
    lidx = latency_idx_a(plr, onset_idx)
    pidx = peak_constriction_idx(plr)
    return np.mean(abs(vel[lidx:pidx]))
    
def max_constriction_velocity(plr, sample_rate, onset_idx):
    '''Return the maximum constriction velocity.
    
    '''
    vel  = velocity_profile(plr, sample_rate)
    pidx = peak_constriction_idx(plr)
    return np.max(abs(vel[onset_idx:pidx]))

def max_constriction_acceleration(plr, sample_rate, onset_idx):
    '''Return the maximum constriction acceleration.
    
    '''
    acc  = acceleration_profile(plr, sample_rate)
    pidx = peak_constriction_idx(plr)
    return np.max(abs(acc[onset_idx:pidx]))

def constriction_time(plr, sample_rate, onset_idx):
    '''Return the time difference between constriction latency and peak 
    constriction.
    
    '''
    lat  = latency_to_constriction_a(plr, sample_rate, onset_idx)
    ttmc = time_to_max_constriction(plr, sample_rate, onset_idx)
    return  ttmc - lat

def max_redilation_velocity(plr, sample_rate):
    '''Return the maximum redilation velocity.
    
    '''
    vel  = velocity_profile(plr, sample_rate)
    pidx = peak_constriction_idx(plr)
    return np.max(abs(vel[pidx:])) 

def max_redilation_acceleration(plr, sample_rate):
    '''Return the maximum redilation acceleration.
    
    '''   
    acc  = acceleration_profile(plr, sample_rate)
    pidx = peak_constriction_idx(plr)
    return np.max(abs(acc[pidx:]))

def time_to_75pc_recovery(plr, sample_rate, onset_idx):
    '''Return the time in ms until 75% recovery from baseline.
    
    '''
    base = baseline(plr, onset_idx)
    pidx = peak_constriction_idx(plr)
    amp  = constriction_amplitude(plr, onset_idx)
    return np.argmax(plr[pidx:] > base - (amp / 4)) * (1000 / sample_rate)

def plr_parameters(plr, sample_rate, onset_idx):
    '''Collapse a PLR into descriptive parameters.
    
    Parameters
    ----------
    plr : array-like
        Data representing a pupil's response to light in mm units.
    sample_rate : int
        sampling rate of the measurement system.
    onset_idx : int
        index of the onset of the light stimulus.
        
    Returns
    -------
    params : pd.DataFrame
        DataFrame containins the params.
    '''
    
    params = {
        'Baseline': baseline(plr, onset_idx),
        'Latency_a': latency_to_constriction_a(plr, sample_rate, onset_idx),
        'Latency_b': latency_to_constriction_b(plr, sample_rate, onset_idx),
        'T2MaxVel': time_to_max_velocity(plr, sample_rate, onset_idx),
        'T2MaxCon': time_to_max_constriction(plr, sample_rate, onset_idx),
        'T2Rec75pc': time_to_75pc_recovery(plr, sample_rate, onset_idx),
        'PeakCon': peak_constriction(plr),
        'ConAmplitude': constriction_amplitude(plr, onset_idx),
        'VelConMax': max_constriction_velocity(plr, sample_rate, onset_idx),
        'VelConAve': average_constriction_velocity(plr, sample_rate, onset_idx),
        'AccConMax': max_constriction_acceleration(plr, sample_rate, onset_idx),
        'ConTime': constriction_time(plr, sample_rate, onset_idx),
        'VelRedMax': max_redilation_velocity(plr, sample_rate),
        'AccRedMax': max_redilation_acceleration(plr, sample_rate)
        }
    return pd.DataFrame.from_dict(params, orient='index', columns=['value'])

def plot_plr(plr, 
             onset_idx, 
             stim_dur,
             sample_rate,
             vel_acc=True,
             print_params=True):
    '''Plot a PLR with option to add descriptive parameters and velocity / 
    acceleration profiles. 
    
    Parameters
    ----------
    plr : array like
        Data representing a pupil's response to a flash of light. Ideally 
        smoothed and for best results an average of multiple trials.
    sample_rate : int
        Sampling rate of the measurement system.
    onset_idx : int
        Index of the onset of the light stimulus.
    stim_dur : float
        Duration (s) of the light stimulus.
    vel_acc : bool, optional
        Whether to also plot the velocity and acceleration profiles.
        The default is False.
    stamp_metrics : bool, optional
        Whether to annotate the axis with the results of a call to 
        ``plr_metrics(...)``. The default is False.
        
    Returns
    -------
    fig : matplotlib.figure.Figure
        The plot.
        
    '''
    t_max = len(plr) / sample_rate
    time = np.linspace(0, t_max, num=len(plr)) - (onset_idx / sample_rate)
    b = baseline(plr, onset_idx)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(time, plr, lw=4)
    ax.axhline(b, 0, 1, ls='dashed', color='k', lw=1)
    ax.axvspan(0, 0 + stim_dur, color='k', alpha=.3)
    ax.set_ylabel('Pupil Size')
    ax.set_xlabel('Time (s)')
    
    if vel_acc:
        ax2 = ax.twinx()
        vel = velocity_profile(plr, sample_rate)
        acc = acceleration_profile(plr, sample_rate)
        ax2.plot(time, vel, color='g', lw=2.5)
        ax2.plot(time, acc, color='r', lw=1)
        ax2.set_ylabel('Velocity / Acceleration')
    
    if print_params:
        m = plr_parameters(plr, sample_rate, onset_idx)
        m = m.round(3)
        ax.text(.78, .03, m.to_string(), size=8, transform=ax.transAxes)
            
    return fig

##########################################
# FUNCTIONS FOR CALCULATING PIPR METRICS #
##########################################

def pipr_amplitude(plr, sample_rate, window):
    return plr[window[0]:window[1]].mean()
 
def pipr_duration(plr, sample_rate, onset_idx, duration):
    '''
    Return the time to return to baseline after light offset. ISI should be 
    between 100 and 660 s to allow pupil to return to baseline (see Adhikari
    et al., 2015)
    '''
    offset_idx = onset_idx + duration
    base = baseline(plr, onset_idx)
    return np.argmax(plr[offset_idx:] >= base) * (1000 / sample_rate)

def pipr_AUC_early(plr, sample_rate, onset_idx, duration):
    '''
    Unitless - AUC between offset and 10 s post offset
    '''
    base = baseline(plr, onset_idx)
    offset_idx = onset_idx + duration
    auc_idx = offset_idx + (sample_rate * 10)
    return np.sum(base - abs(plr[offset_idx:auc_idx]))

def pipr_AUC_late(plr, sample_rate, onset_idx, duration):
    '''
    Unitless - AUC between 10-30 s post offset
    '''
    base = baseline(plr, onset_idx)
    offset_idx = onset_idx + duration
    auc_idx = offset_idx + (sample_rate * 10)
    return np.sum(base - abs(plr[auc_idx:auc_idx + (sample_rate * 30)]))
    
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