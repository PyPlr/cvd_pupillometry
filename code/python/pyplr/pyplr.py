# -*- coding: utf-8 -*-
'''
Created on Mon Mar 30 17:05:47 2020
@author: JTM
note: credit to Acland BT, Braver TS (2014) for some of this code
https://github.com/beOn/cili
Acland BT, Braver TS (2014). Cili (v0.5.4) [Software] 
Available from http://doi.org/10.5281/zenodo.48843. doi:10.5281/zenodo.48843
'''

import os
import shutil
import os.path as op
from copy import deepcopy

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

##########################
# FUNCTIONS TO LOAD DATA #
##########################

def init_subject_analysis(subjdir, out_dir_nm='analysis'):
    '''
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
    dict
        information for the subject.
    '''
    subjid = op.basename(subjdir)
    print('{}\n{:*^60s}\n{}'.format('*'*60,subjid,'*'*60,))
    pl_data_dir = op.join(subjdir, 'exports\\000') # default for data exported from pupil player
    out_dir = op.join(subjdir, out_dir_nm)
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.mkdir(out_dir)
    return {
        'id':subjid,
        'root':subjdir,
        'pl_data_dir':pl_data_dir, 
        'out_dir':out_dir
        }

def load_annotations(data_dir):
    '''
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
    '''
    events = pd.read_csv(data_dir + '\\annotations.csv')
    print('Loaded {} events'.format(len(events)))
    return events
   
def load_pupil(data_dir, method='3d c++', cols=[]):
    '''
    Loads "pupil_positions" data exported from Pupil Player.
    
    Parameters
    ----------
    data_dir : str
        Directory where the Pupil Labs 'annotations' data exists.
    cols : list
        Columns to load from the file, e.g. ["pupil_timestamp","diameter","diameter_3d"]
        (check file for options). The default is ["pupil_timestamp","diameter"].
    Returns
    -------
    samps : DataFrame
        Pandas DataFrame containing requested samples.
    '''
    if not cols:
        samps = pd.read_csv(data_dir + '\\pupil_positions.csv')
    else:
        samps = pd.read_csv(data_dir + '\\pupil_positions.csv', usecols=cols)
    samps = samps[samps.method=='3d c++']    
    samps.set_index('pupil_timestamp', inplace=True)
    print('Loaded {} samples'.format(len(samps)))
    return samps

def load_blinks(data_dir):
    '''
    Loads "blinks" data exported from Pupil Player.
    Parameters
    ----------
    data_dir : str
        Directory where the Pupil Labs "blinks" data exists.
    Returns
    -------
    blinks : DataFrame
        Pandas DataFrame containing blink events.
    '''
    blinks = pd.read_csv(data_dir + '\\blinks.csv')
    print('{} blinks detected by Pupil Labs, average duration {:.3f} s'.format(
        len(blinks), blinks.duration.mean()))
    return blinks    

###########################
# FUNCTIONS TO CLEAN DATA #
###########################
    
def ev_row_idxs(samples, blinks):
    ''' 
    Returns the indices in "samples" contained in events from "events".
    Parameters
    ----------
    samples : DataFrame
        The samples from which to pull indices.
    events : DataFrame
        The events whose indices should be pulled from "samples".
    '''
    idxs = []
    for start, end in zip(blinks['start_timestamp'],blinks['end_timestamp']):
        #print(start, end)
        idxs.extend(list(samples.loc[start:end].index))
    idxs = np.unique(idxs)
    idxs = np.intersect1d(idxs, samples.index.tolist())
    return idxs

def get_mask_idxs(samples, blinks):
    '''
    Finds indices from "samples" within the returned events.
    '''
    blidxs = ev_row_idxs(samples, blinks)
    return blidxs

def mask_blinks(samples, blinks, mask_cols=['diameter']):
    '''
    Sets untrustworthy pupil data to NaN.
    
    Parameters
    ----------
    samples : DataFrame
        must contain at least "pupil_timestamp" and "diameter" columns
    blinks : DataFrame
        must contain "start_timestamp" and "end_timestamp" columns
    mask_cols : list, optional
        columns to mask. The default is ["diameter"].
    Returns
    -------
    samps : DataFrame
        masked data
    '''
    samps = samples.copy(deep=True)
    indices = get_mask_idxs(samps, blinks)
    samps.loc[indices, mask_cols] = float('nan')
    samps['interpolated'] = 0
    samps.loc[indices, 'interpolated'] = 1
    return samps

def interpolate_blinks(samples, blinks, fields=['diameter']):
    '''
    Reconstructs Pupil Labs eye blinks with linear interpolation.
    
    Parameters
    ----------
    samples : DataFrame
        must contain at least "pupil_timestamp" and "diameter" columns
    blinks : DataFrame
        must contain "start_timestamp" and "end_timestamp" columns
    interp_cols : list, optional
        columns to interpolate. The default is ["diameter"].
    Returns
    -------
    samps : DataFrame
        blink-interpolated data
    '''
    samps = mask_blinks(samples, blinks, mask_cols=fields)
    samps = samps.interpolate(method='linear', axis=0, inplace=False)
    
    print('{} samples ({:.3f} %) reconstructed with linear interpolation'.format(
        len(samps.loc[samps['interpolated']==1]), 
        samps.loc[:,'interpolated'].value_counts(normalize=True)[1]*100))
    return samps

def mask_zeros(samples, mask_cols=['diameter']):
    ''' 
    Sets any 0 values in columns in mask_cols to NaN.
    
    Parameters
    ----------
    samples : DataFrame
        The samples to search for 0 values.
    mask_fields (list of strings)
        The columns to search for 0 values.
    '''
    samps = samples.copy(deep=True)
    for f in mask_cols:
        samps[samps[f] == 0] = float('nan')
    return samps

def interpolate_zeros(samples, fields=['diameter']):
    ''' 
    Replace 0s in "samples" with linearly interpolated data.
    Parameters
    ----------
    samples : DataFrame
        The samples in which you'd like to replace 0s
    interp_cols : list
        The column names from samples in which you'd like to replace 0s.
    '''
    samps = mask_zeros(samples, mask_cols=fields)
    samps = samps.interpolate(method='linear', axis=0, inplace=False)
    # since interpolate doesn't handle the start/finish, bfill the ffill to
    # take care of NaN's at the start/finish samps.
    samps.fillna(method='bfill', inplace=True)
    samps.fillna(method='ffill', inplace=True)
    return samps  

def butterworth_series(samples,
                       fields=['diameter'], 
                       filt_order=3,
                       cutoff_freq=.01,
                       inplace=False):
    '''
    Applies a butterworth filter to the given fields
    See documentation on scipy's butter method FMI.
    '''
    import scipy.signal as signal
    samps = samples if inplace else samples.copy(deep=True)
    B, A = signal.butter(filt_order, cutoff_freq, output='BA')
    samps[fields] = samps[fields].apply(
        lambda x: signal.filtfilt(B, A, x), axis=0)
    return samps

def savgol_series(samples, 
                  fields=['diameter'], 
                  window_length=51, 
                  filt_order=7,
                  inplace=False): 
    '''
    Applies a savitsky-golay filter to the given fields
    See documentation on scipys savgol_filter method FMI.
    '''
    import scipy.signal as signal
    samps = samples if inplace else samples.copy(deep=True)
    samps[fields] = samps[fields].apply(
        lambda x: signal.savgol_filter(x, window_length, filt_order), axis=0)
    return samps
    
###########
# extract #
###########
    
def extract(samples, 
            events, 
            offset=0, 
            duration=0,
            borrow_attributes=[]):
    '''
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
        this has to be the same for all events, but could use a 'duration' 
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
    '''
    # negative duration should raise an exception
    if duration <= 0:
        raise ValueError('Duration must be >0')
        
    # get the list of start time indices
    e_starts = events.index.to_series()

    # find the indexes of the event starts, and offset by sample count
    r_idxs = np.searchsorted(samples.index, e_starts.iloc[:], 'left') + offset
    r_dur = duration

    # make a hierarchical index
    samples['orig_idx'] = samples.index
    midx = pd.MultiIndex.from_product(
        [list(range(len(e_starts))), list(range(r_dur))],
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
    
    print('Extracted ranges for {} events'.format(len(events)))
    return df

def reject_bad_trials(ranges, interp_thresh=20, drop=False):
    '''
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
    '''
    if not isinstance(ranges.index, pd.MultiIndex):
        raise ValueError('Index of ranges must be pd.MultiIndex')
        
    pct_interp = ranges.groupby(by='event').agg(
        {'interpolated':lambda x: float(x.sum())/len(x)*100})
    print('Percentage of data interpolated for each trial (mean = {:.2f}): \n'.format(
        pct_interp.mean()[0]), pct_interp)
    reject_idxs = pct_interp.loc[pct_interp['interpolated'] > interp_thresh].index.to_list()
    ranges['reject'] = 0
    if reject_idxs:
        ranges.loc[reject_idxs, 'reject'] = 1
    if drop:
        ranges = ranges.drop(index=reject_idxs)
        print('{} trials were dropped from the DataFrame'.format(len(reject_idxs)))
    else:
        print('{} trials were marked for rejection'.format(len(reject_idxs)))
    return ranges

#########################################
# FUNCTIONS FOR CALCULATING PLR METRICS #
#########################################

def velocity_profile(s, sample_rate):
    t = 1 / sample_rate
    return np.diff(s) / t

def acceleration_profile(s, sample_rate):
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
    vel = velocity_profile(s, sample_rate)
    return np.argmin(vel[onset_idx:]) * (1000 / sample_rate)

def peak_constriction_idx(s):
    '''
    Return the index of the sample with peak constriction.
    '''
    return np.argmin(s)

def peak_constriction(s):
    '''
    Return the peak constriction value.
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

##########################################
# FUNCTIONS FOR CALCULATING PIPR METRICS #
##########################################

def pipr_amplitude(s, sample_rate, window):
     pipr = s[window[0]:window[1]].mean()
     return pipr
 
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
    

def plr_metrics(s, sample_rate, onset_idx, pc):
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
    metrics : pd.DataFrame
        DataFrame containins the metrics.
    '''
    
    metrics = {
               'D1'        : baseline(s, onset_idx),
               'T1a'       : latency_to_constriction_a(s, sample_rate, onset_idx, pc),
               'T1b'       : latency_to_constriction_b(s, sample_rate, onset_idx),
               'T2'        : time_to_max_velocity(s, sample_rate, onset_idx),
               'T3'        : time_to_max_constriction(s, sample_rate, onset_idx),
               'T4'        : recovery_time_75pc(s, sample_rate, onset_idx),
               'D2'        : peak_constriction(s),
               'AMP'       : constriction_amplitude(s, onset_idx),
               'VelConMax' : max_constriction_velocity(s, sample_rate, onset_idx),
               'VelConAve' : average_constriction_velocity(s, sample_rate, onset_idx, pc),
               'AccConMax' : max_constriction_acceleration(s, sample_rate, onset_idx),
               'CT'        : constriction_time(s, sample_rate, onset_idx, pc),
               'VelRedMax' : max_redilation_velocity(s, sample_rate),
               'AccRedMax' : max_redilation_acceleration(s, sample_rate)
               }
    metrics = pd.DataFrame.from_dict(metrics, orient='index')
    return metrics

def plot_plr(s, 
             sample_rate,
             onset_idx, 
             stim_dur,
             vel_acc=False,
             stamp_metrics=False):
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
    b = baseline(s, onset_idx)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(s, lw=3)
    ax.axhline(b, 0, 1, ls='dashed', color='k', lw=1)
    ax.axvspan(onset_idx, onset_idx + (sample_rate * stim_dur), color='k', alpha=.3)
    ax.set_ylabel('Pupil Size')
    ax.set_xlabel('Time (s)')
    x  = [val for val in range(0, len(s), sample_rate * 5)]
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
    
    if stamp_metrics:
        m = plr_metrics(s, sample_rate, onset_idx, pc=.01)
        m = m.round(3)
        ax2.text(.78, .03, m.to_string(), size=8, transform=ax2.transAxes)
            
    return fig

# def plot_trials(ranges, sample_rate, onset_idx, stim_dur, pupil_col='diameter', out_dir=None):
#     if not isinstance(ranges.index, pd.MultiIndex):
#         ranges.set_index(['event','onset'], inplace=True)
#     for event, df in ranges.groupby(level=0):
#         f = plot_plr(df[pupil_col].values, sample_rate, onset_idx, stim_dur, vel_acc=True, stamp_metrics=True)
#         if out_dir:
#             f.savefig(out_dir + '\\event' + str(event) + '.png')