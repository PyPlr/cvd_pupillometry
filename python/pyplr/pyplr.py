# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 17:05:47 2020

@author: engs2242
"""

import pandas as pd
import numpy as np
from copy import deepcopy

# functions to load data
def load_annotations(data_dir):
    events = pd.read_csv(data_dir + "annotations.csv")
    return events
   
def load_pupil(data_dir):
    samples = pd.read_csv(data_dir + "pupil_positions.csv", index_col="pupil_timestamp")
    return samples

def load_blinks(data_dir):
    blinks = pd.read_csv(data_dir + "blinks.csv")
    return blinks    

# functions to clean data
def ev_row_idxs(samples, blinks):
    """ 
    Returns the indices in 'samples' contained in events from 'events.'
    Parameters
    ----------
    samples : DataFrame
        The samples from which to pull indices.
    events : DataFrame
        The events whose indices should be pulled from 'samples'.
    """
    idxs = []
    for start, end in zip(blinks["start_timestamp"],blinks["end_timestamp"]):
        print(start, end)
        idxs.extend(list(samples.loc[start:end].index))
    idxs = np.unique(idxs)
    idxs = np.intersect1d(idxs, samples.index.tolist())
    return idxs

def get_mask_idxs(samples, blinks):
    """
    Finds indices from 'samples' within the returned events.
    """
    blidxs = ev_row_idxs(samples, blinks)
    return blidxs

def mask_blinks(samples, blinks, mask_cols=["diameter"]):
    """
    Sets untrustworthy pupil data to NaN.
    
    Parameters
    ----------
    samples : DataFrame
        must contain at least 'pupil_timestamp' and 'diameter' columns
    blinks : DataFrame
        must contain 'start_timestamp' and 'end_timestamp' columns
    mask_cols : list, optional
        columns to mask. The default is ["diameter"].

    Returns
    -------
    samps : DataFrame
        masked data
    """
    samps = samples.copy(deep=True)
    indices = get_mask_idxs(samps, blinks)
    samps.loc[indices, mask_cols] = float('nan')
    return samps

def interpolate_blinks(samples, blinks, interp_cols=["diameter"]):
    """
    Reconstructs Pupil Labs eye blinks with linear interpolation.
    
    Parameters
    ----------
    samples : DataFrame
        must contain at least 'pupil_timestamp' and 'diameter' columns
    blinks : DataFrame
        must contain 'start_timestamp' and 'end_timestamp' columns
    interp_cols : list, optional
        columns to interpolate. The default is ["diameter"].
    Returns
    -------
    samps : DataFrame
        blink-interpolate data
    """
    samps = mask_blinks(samples, blinks, mask_cols=interp_cols)
    samps = samps.interpolate(method="linear", axis=0, inplace=False)
    return samps
    
def butterworth_series(samples, fields=["diameter"], filt_order=5, cutoff_freq=.01, inplace=False):
    """
    Applies a butterworth filter to the given fields
    See documentation on scipy's butter method FMI.
    """
    import scipy.signal as signal
    samps = samples if inplace else samples.copy(deep=True)
    B, A = signal.butter(filt_order, cutoff_freq, output="BA")
    samps[fields] = samps[fields].apply(
        lambda x: signal.filtfilt(B, A, x), axis=0)
    return samps

# def downsample(samples):
#     return samps

# function to extract events
def extract_events(samples, events, offset=0, duration=0,
                   borrow_attributes=[], return_count=False):
    """
    Extracts ranges from samples based on event timing and sample count.
    """
    # negative duration should raise an exception
    if duration <= 0:
        raise ValueError("Duration must be >0")
    # get the list of start time indices
    e_starts = events.index.to_series()

    # find the indexes of the event starts, and offset by sample count
    r_idxs = np.searchsorted(samples.index, e_starts.iloc[:], 'left') + offset
    r_dur = duration

    # make a hierarchical index
    samples['orig_idx'] = samples.index
    midx = pd.MultiIndex.from_product([list(range(len(e_starts))), list(range(r_dur))],
                                      names=['event', 'onset'])
    # get the samples
    df = pd.DataFrame()
    idx = 0
    for s_idx in r_idxs:
        # get the start time and add the required number of indices
        e_idx = s_idx + r_dur - 1  # pandas.loc indexing is inclusive
        # deepcopy for old bugs
        new_df = deepcopy(
            samples.loc[samples.index[s_idx]: samples.index[e_idx]])
        for ba in borrow_attributes:
            new_df[ba] = events.iloc[idx].get(ba, float('nan'))
        df = pd.concat([df, new_df])
        idx += 1
    df.index = midx
    return df

# functions for plr metrics
def baseline(s, onset_idx):
    """
    Return the average pupil size between the start of s and onset_idx
    """
    baseline = s[0:onset_idx].mean()
    return baseline

def latency_idx(s, sample_rate, onset_idx, pc=None):
    """
    Return the index of the first sample following stimulus onset where 
    constriction exceeds a percentage of the baseline.
    """
    if pc is None:
        raise ValueError("Must specify int or float for pc")
    b = baseline(s, onset_idx)
    if isinstance(pc, float):
        threshold = b-(b*pc)
        lidx = np.argmax(s[onset_idx:]<threshold)
    elif isinstance(pc, int):
        threshold = b-pc
        lidx = np.argmax(s[onset_idx:]<threshold)
    return lidx

def latency_to_constriction(s, sample_rate, onset_idx, pc=None):
    """
    Return the time in miliseconds between stimulus onset and the first 
    sample where constriction exceeds a percentage of the baseline.
    """
    lidx = latency_idx(s, sample_rate, onset_idx, pc=pc)
    latency = lidx / (sample_rate/1000)
    return latency  

def time_to_peak_constriction(s, sample_rate, onset_idx):
    """
    Return the time in miliseconds between stimulus onset and the peak 
    of pupil constriction.
    """
    ttpc = (np.argmin(s)-onset_idx)/(sample_rate/1000)
    return ttpc

def peak_constriction(s, onset_idx):
    """
    Return the peak constriction value.
    """
    peak = np.min(s[onset_idx:])
    return peak

def maximum_constriction_amplitude(s, onset_idx):
    """
    Return the absolute difference between baseline and peak constriction.
    """
    peak = peak_constriction(s, onset_idx)
    b = baseline(s, onset_idx)
    mca = abs(peak-b)
    return mca

def maximum_constriction_velocity(s, sample_rate):
    """
    Return the maximum_constriction_velocity.
    """
    t = 1/sample_rate
    v = s.diff()/t
    mcv = v.max()
    return mcv

def constriction_time(s, sample_rate, onset_idx, pc=None):
    """
    Return the time difference between constriction latency and peak constriction.
    """
    latency = latency_to_constriction(s, sample_rate, onset_idx, pc)
    ttpc = time_to_peak_constriction(s, sample_rate, onset_idx)
    ct = ttpc-latency
    return ct

# def pipr(s, onset_idx, duration):
#     pipr = s[onset_idx+duration:].mean()
#     return pipr

# def get_plr_metrics(averages, group_level, pupil_col, onset_time, sample_rate, pc):
#     return metrics