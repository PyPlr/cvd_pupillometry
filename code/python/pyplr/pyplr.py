# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 17:05:47 2020

@author: JTM

note: credit to Acland BT, Braver TS (2014) for some of this code
https://github.com/beOn/cili

Acland BT, Braver TS (2014). Cili (v0.5.4) [Software] 
Available from http://doi.org/10.5281/zenodo.48843. doi:10.5281/zenodo.48843
"""

import os
import shutil
import os.path as op
import pandas as pd
import numpy as np
from copy import deepcopy

##########################
# FUNCTIONS TO LOAD DATA #
##########################

def init_subject_analysis(subjdir, out_dir_nm="analysis"):
    """
    Initiate data analysis for a given subject.
    
    Parameters
    ----------
    subjdir : str
        Path to subject directory
    out_dir_nm : str, optional
        Name for the new directory where analysis results will be saved. 
        The default is "analysis".

    Returns
    -------
    subjid : str
        id of the current subject
    pl_data_dir : str
        Directory where the Pupil Labs data exists
    out_dir : str
        New directory to save results of current analysis
    """
    subjid = op.basename(subjdir)
    print("{}\n{:*^60s}\n{}".format("*"*60,subjid,"*"*60,))
    pl_data_dir = op.join(subjdir, "exports\\000") # default for data exported from pupil player
    out_dir = op.join(subjdir, out_dir_nm)
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.mkdir(out_dir)
    return subjid, pl_data_dir, out_dir

def load_annotations(data_dir):
    """
    Loads annotations (a.k.a. "triggers", "events", etc.) exported 
    from Pupil Player.

    Parameters
    ----------
    data_dir : str
        Directory where the Pupil Labs "annotations" data exists.

    Returns
    -------
    events : DataFrame
        Pandas DataFrame containing events.
    """
    events = pd.read_csv(data_dir + "\\annotations.csv")
    print("Loaded {} events".format(len(events)))
    return events
   
def load_pupil(data_dir, cols=["pupil_timestamp","diameter"]):
    """
    Loads "pupil_positions" data exported from Pupil Player.

    Parameters
    ----------
    data_dir : str
        Directory where the Pupil Labs "annotations" data exists.
    cols : list
        Columns to load from the file, e.g. ["pupil_timestamp","diameter","diameter_3d"]
        (check file for options). The default is ["pupil_timestamp","diameter"].

    Returns
    -------
    samps : DataFrame
        Pandas DataFrame containing requested samples.
    """
    samps = pd.read_csv(data_dir + "\\pupil_positions.csv", usecols=cols)
    samps.set_index("pupil_timestamp", inplace=True)
    print("Loaded {} samples".format(len(samps)))
    return samps

def load_blinks(data_dir):
    """
    Loads "blinks" data exported from Pupil Player.

    Parameters
    ----------
    data_dir : str
        Directory where the Pupil Labs "blinks" data exists.

    Returns
    -------
    blinks : DataFrame
        Pandas DataFrame containing blink events.

    """
    blinks = pd.read_csv(data_dir + "\\blinks.csv")
    print("{} blinks detected by Pupil Labs, average duration {:.3f} s".format(len(blinks), blinks.duration.mean()))
    return blinks    

###########################
# FUNCTIONS TO CLEAN DATA #
###########################
    
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
        #print(start, end)
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
    samps["interpolated"] = 0
    samps.loc[indices, "interpolated"] = 1
    return samps

def interpolate_blinks(samples, blinks, fields=["diameter"]):
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
        blink-interpolated data
    """
    samps = mask_blinks(samples, blinks, mask_cols=fields)
    samps = samps.interpolate(method="linear", axis=0, inplace=False)
    
    print("{} samples ({:.3f} %) reconstructed with linear interpolation".format(
        len(samps.loc[samps["interpolated"]==1]), 
        samps.loc[:,"interpolated"].value_counts(normalize=True)[1]*100))
    return samps

def mask_zeros(samples, mask_cols=["diameter"]):
    """ 
    Sets any 0 values in columns in mask_cols to NaN.
    
    Parameters
    ----------
    samples : DataFrame
        The samples you'd like to search for 0 values.
    mask_fields (list of strings)
        The columns in you'd like to search for 0 values.
    """
    samps = samples.copy(deep=True)
    for f in mask_cols:
        samps[samps[f] == 0] = float("nan")
    return samps

def interpolate_zeros(samples, fields=["diameter"]):
    """ 
    Replace 0s in 'samples' with linearly interpolated data.
    Parameters
    ----------
    samples : DataFrame
        The samples in which you'd like to replace 0s
    interp_cols : list
        The column names from samples in which you'd like to replace 0s.
    """
    samps = mask_zeros(samples, mask_cols=fields)
    samps = samps.interpolate(method="linear", axis=0, inplace=False)
    # since interpolate doesn't handle the start/finish, bfill the ffill to
    # take care of NaN's at the start/finish samps.
    samps.fillna(method="bfill", inplace=True)
    samps.fillna(method="ffill", inplace=True)
    return samps  

def butterworth_series(samples, fields=["diameter"], filt_order=3, cutoff_freq=.01, inplace=False):
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

def savgol_series(samples, fields=["diameter"], window_length=51, filt_order=7, inplace=False): 
    """
    Applies a savitsky-golay filter to the given fields
    See documentation on scipy's savgol_filter method FMI.
    """
    import scipy.signal as signal
    samps = samples if inplace else samples.copy(deep=True)
    samps[fields] = samps[fields].apply(
        lambda x: signal.savgol_filter(x, window_length, filt_order), axis=0)
    return samps
    
###########
# extract #
###########
    
def extract(samples, events, offset=0, duration=0, borrow_attributes=[]):
    """
    Extracts ranges from samples based on event timing and sample count.

    Parameters
    ----------
    samples : DataFrame
        The samples to extract from. Index must be timestamp.
    events : DataFrame
        The events to extract. Index must be timestamp.
    offset : int, optional
        Number of samples to offset from baseline. The default is 0.
    duration : int, optional
        Duration of all events in terms of the number of samples. Currently 
        this has to be the same for all events, but could use a "duration" 
        column in events DataFrame if needs be. The default is 0.
    borrow_attributes : list of str, optional
        List of column names in the events DataFrame whose values should be
        copied to the respective ranges. For each item in the list, a
        column will be created in the ranges dataframe - if the column does
        not exist in the events dataframe, the values in the each
        corresponding range will be set to float('nan'). This is uesful for 
        marking conditions, grouping variables, etc. The default is [].

    Returns
    -------
    df : DataFrame
        Extracted events complete with hierarchical multi-index.
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
    
    print("Extracted ranges for {} events".format(len(events)))
    return df

def reject_bad_trials(ranges, interp_thresh=20, drop=False):
    """
    Drop or markup trials which exceed a threshold of interpolated data.

    Parameters
    ----------
    ranges : DataFrame
        Extracted event ranges with hierarchical pd.MultiIndex.
    interp_thresh : int, optional
        Percentage of interpolated data permitted before trials are marked for
        rejection / dropped. The default is 20.
    drop : bool, optional
        Whether to drop the trials from the ranges. The default is False.

    Returns
    -------
    ranges : DataFrame
        Same as ranges but with a column identifying trials marked for
        rejection (drop = False) or with those trials dropped from the 
        DataFrame (drop = True).
    """
    if not isinstance(ranges.index, pd.MultiIndex):
        raise ValueError("Index of ranges must be pd.MultiIndex")
        
    pct_interp = ranges.groupby(by="event").agg(
        {'interpolated':lambda x: float(x.sum())/len(x)*100})
    print("Percentage of data interpolated for each trial (mean = {:.2f}): \n".format(
        pct_interp.mean()[0]), pct_interp)
    reject_idxs = pct_interp.loc[pct_interp["interpolated"] > interp_thresh].index.to_list()
    ranges["reject"] = 0
    if reject_idxs:
        ranges.loc[reject_idxs, "reject"] = 1
    if drop:
        ranges = ranges.drop(index=reject_idxs)
        print("{} trials were dropped from the DataFrame".format(len(reject_idxs)))
    else:
        print("{} trials were marked for rejection".format(len(reject_idxs)))
    return ranges

#########################################
# FUNCTIONS FOR CALCULATING PLR METRICS #
#########################################

def baseline(s, onset_idx):
    """
    Return the average pupil size between the start of s and onset_idx
    """
    baseline = s[0:onset_idx].mean()
    return baseline

def latency_idx(s, sample_rate, onset_idx, pc=None):
    """
    Return the index of the first sample following stimulus onset where 
    constriction exceeds a percentage of the baseline. pc should be int or
    float for data already expressed as pc (e.g. pc=1 == pc=.01)
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
    lidx += onset_idx
    return lidx

def latency_to_constriction(s, sample_rate, onset_idx, pc=None):
    """
    Return the time in miliseconds between stimulus onset and the first 
    sample where constriction exceeds a percentage of the baseline.
    """
    lidx = latency_idx(s, sample_rate, onset_idx, pc=pc)
    latency = (lidx-onset_idx) / (sample_rate/1000)
    return latency  

def time_to_peak_constriction(s, sample_rate, onset_idx):
    """
    Return the time in miliseconds between stimulus onset and the peak 
    of pupil constriction.
    """
    ttpc = (np.argmin(s)-onset_idx)/(sample_rate/1000)
    return ttpc

def peak_constriction_idx(s):
    """
    Return the index of the sample with peak constriction.
    """
    pidx = np.argmin(s)
    return pidx

def peak_constriction(s, onset_idx):
    """
    Return the peak constriction value.
    """
    peakcon = np.min(s)
    return peakcon

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
    mcv = v.min() # minimum of velocity profile for constriction
    return mcv

def maximum_constriction_acceleration(s, sample_rate):
    t = 1/sample_rate
    v = s.diff()/t
    acc = v.diff()/t
    mcacc = acc.min() # minimum of acceleration profile for constriction
    return mcacc

def constriction_time(s, sample_rate, onset_idx, pc=None):
    """
    Return the time difference between constriction latency and peak constriction.
    """
    latency = latency_to_constriction(s, sample_rate, onset_idx, pc)
    ttpc = time_to_peak_constriction(s, sample_rate, onset_idx)
    ct = ttpc-latency
    return ct

def maximum_redilation_velocity(s, sample_rate):
    """
    Return the maximum_dilation_velocity.
    """
    t = 1/sample_rate
    v = s.diff()/t
    mcv = v.max() # maximum of velocity profile for redilation
    return mcv

def maximum_redilation_acceleration(s, sample_rate):
    t = 1/sample_rate
    v = s.diff()/t
    acc = v.diff()/t
    mcacc = acc.max() # maximum of acceleration profile for redilation
    return mcacc

# def pipr(s, onset_idx, duration):
#     pipr = s[onset_idx+duration:].mean()
#     return pipr

def get_plr_metrics(s, sample_rate, onset_idx, pc):
    """
    Collapse a PLR into descriptive parameters.

    Parameters
    ----------
    s : pd.Series
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
    metrics : pd.DataFrame
        DataFrame containins the metrics.
    """
    
    metrics = {
               "B"     : [baseline(s, onset_idx)],
               "LTC"   : [latency_to_constriction(s, sample_rate, onset_idx, pc)],
               "TTPC"  : [time_to_peak_constriction(s, sample_rate, onset_idx)],
               "PC"    : [peak_constriction(s, onset_idx)],
               "MCAmp" : [maximum_constriction_amplitude(s, onset_idx)],
               "MCVel" : [maximum_constriction_velocity(s, sample_rate)],
               "MCAcc" : [maximum_constriction_acceleration(s, sample_rate)],
               "CT"    : [constriction_time(s, sample_rate, onset_idx, pc)],
               "MRVel" : [maximum_redilation_velocity(s, sample_rate)],
               "MRAcc" : [maximum_redilation_acceleration(s, sample_rate)]
               }
    metrics = pd.DataFrame.from_dict(metrics, orient='columns')
    return metrics


    

