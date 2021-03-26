#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
pyplr.preproc
=============

Scripting tools for preprocessing pupil data.

@author: jtm

'''

import numpy as np
import scipy.signal as signal


def even_samples(samples, sample_rate, fields=['diameter'], zero_index=False):
    '''Resample  data in `fields` to a new index with evenly spaced timepoints.

    Pupil Core data samples are unevenly spaced. 
    
    Parameters
    ----------
    samples : pandas.DataFrame
        The samples.
    sample_rate : int
        Sampling rate of the data.
    fields : list, optional
        The columns to interpolate to new index. The default is ['diameter'].

    Returns
    -------
    samps : pandas.DataFrame
        DataFrame with evenly spaced index and interpolated data.

    '''
    # TODO: When is the best time to do this?
    samps = samples.copy(deep=True)
    x = samps.index.to_numpy()
    if zero_index:
        x = x - x[0]
    xnew = np.linspace(x.min(), x.max(), len(x))
    for f in fields:
        y = samps[f].to_numpy()
        samps[f] = np.interp(xnew, x, y)
    samps.index = xnew
    return samps

def even_range_samples(rangs, sample_rate, fields=[]):
    for idx, df in rangs.groupby(level=['event']):
        for f in fields:
            x = df.orig_idx.to_numpy()
            x = x - x[0]
            xnew = np.linspace(x.min(), x.max(), len(x))
            y = df.loc[idx, f]
            rangs.loc[idx, f] = np.interp(xnew, x, y)
            rangs.loc[idx, 'even_idx'] = xnew
    return rangs

def mask_pupil_first_derivative(samples, 
                                threshold=3.0,
                                mask_cols=['diameter']):
    '''Apply a masking threshold on the first derivative of pupil data.
    
    Use a statistical criterion on the first derivative of pupil data to mask 
    poor quality data. Helpful for dealing with blinks. 

    Parameters
    ----------
    samples : pandas.DataFrame
        Samples containing the data to be masked.
    threshold : float, optional
        Number of standard deviations from the mean of the first derivative 
        to use as the threshold for masking. The default is 3.0.
    mask_cols : list, optional
        Columns to mask. The default is ``['diameter']``.

    Returns
    -------
    samps : pandas.DataFrame
        masked data

    '''
    samps = samples.copy(deep=True)
    for col in mask_cols:
        d = samps[col].diff()
        m = samps[col].diff().mean()
        s = samps[col].diff().std() * threshold
        #TODO: check this works properly
        samps[col] = samps[col].mask((d < (m-s)) | (d > (m+s)))
        samps.loc[samps[col]==0, col] = np.nan
    return samps

def mask_pupil_confidence(samples, threshold=.8, mask_cols=['diameter']):
    '''
    Sets data in mask_cols to NaN where the corresponding confidence metric is
    below threshold. Pupil Labs reccommend a threshold of 0.8. Helpful for
    dealing with blinks. 

    Parameters
    ----------
    samples : pandas.DataFrame
        Samples containing the data to be masked.
    threshold : float, optional
        Confidence threshold for masking. The default is 0.8.
    mask_cols : list, optional
        Columns to mask. The default is ['diameter'].

    Returns
    -------
    samps : pandas.DataFrame
        masked data

    '''
    samps = samples.copy(deep=True)
    samps[mask_cols] = samps[mask_cols].mask(samps.confidence < threshold)
    return samps
    
def pupil_confidence_filter(samples, threshold=.8, mask_cols=['diameter']):
    '''
    Sets data in mask_cols to NaN where the corresponding confidence metric is
    below threshold. Pupil Labs reccommend a threshold of .8. An alterntive
    to interpolating blinks. 

    Parameters
    ----------
    samples : pandas.DataFrame
        The samples from which to pull indices.
    threshold : float, optional
        Threshold to use for filtering by confidence. The default is .8.
    mask_cols : list, optional
        Columns to mask. The default is ['diameter'].

    Returns
    -------
    samps : pandas.DataFrame
        Masked data.
        
    '''
    
    samps = samples.copy(deep=True)
    indices = samples[samples.confidence<threshold].index
    samps.loc[indices, mask_cols] = float('nan')
    samps['interpolated'] = 0
    samps.loc[indices, 'interpolated'] = 1
    return samps

def interpolate_pupil(samples, interp_cols=['diameter'], 
                      method='linear', order=None):
    '''
    Use linear interpolation to reconstruct nan values in interp_cols.

    Parameters
    ----------
    samples : pandas.DataFrame
        Samples containing the data to be interpolated.
    interp_cols : list, optional
        Columns to interpolate. The default is ['diameter'].
    method : string
        Linear or polynomial. If polynomial, requires 'order' to be specified.

    Returns
    -------
    samps : pandas.DataFrame
        Masked data

    '''
    if method=='polynomial' and not order:
        raise ValueError('Must specify order for polynomial')
    samps = samples.copy(deep=True)
    samps['interpolated'] = 0
    samps.loc[samps[interp_cols].isna().any(axis=1), 'interpolated'] = 1
    samps[interp_cols] = samps[interp_cols].interpolate(
        method=method,
        order=order,
        axis=0, 
        inplace=False,
        limit=10000,
        limit_direction='both')
    return samps

def percent_signal_change(ranges, baselines, pupil_cols=[]):
    '''Add new columns expressing pupil_cols as percent change from baseline.
    
    Parameters
    ----------
    ranges : pandas.DataFrame
        DataFrame with MultiIndex. Usually the output from ``utils.extract(...)``
    baselines : TYPE
        DESCRIPTION.
    pupil_cols : TYPE, optional
        DESCRIPTION. The default is [].

    Returns
    -------
    ranges : pandas.DataFrame
        Original DataFrame with new columns for percent-signal change.

    '''
    for col in pupil_cols:
        new_col = col + '_pc'
        ranges[new_col] = (ranges[col] / baselines[col] - 1).values * 100
    return ranges
    
    
def ev_row_idxs(samples, blinks):
    ''' 
    Returns the indices in 'samples' contained in events from 'events'.
    
    Parameters
    ----------
    samples : pandas.DataFrame
        The samples from which to pull indices.
    events : pandas.DataFrame
        The events whose indices should be pulled from 'samples'.
        
    Returns
    -------
    samps : pandas.DataFrame
        Masked data
        
    '''
    idxs = []
    for start, end in zip(blinks['start_timestamp'], blinks['end_timestamp']):
        idxs.extend(list(samples.loc[start:end].index))
    idxs = np.unique(idxs)
    idxs = np.intersect1d(idxs, samples.index.tolist())
    return idxs

def get_mask_idxs(samples, blinks):
    '''
    Finds indices from 'samples' within the returned events.
    
    '''
    blidxs = ev_row_idxs(samples, blinks)
    return blidxs

def mask_blinks(samples, blinks, mask_cols=['diameter']):
    '''
    Sets untrustworthy pupil data to NaN.
    
    Parameters
    ----------
    samples : pandas.DataFrame
        Must contain at least 'pupil_timestamp' and 'diameter' columns
    blinks : pandas.DataFrame
        Must contain 'start_timestamp' and 'end_timestamp' columns
    mask_cols : list, optional
        Columns to mask. The default is ['diameter'].
    Returns
    -------
    samps : pandas.DataFrame
        Masked data
        
    '''
    samps = samples.copy(deep=True)
    indices = get_mask_idxs(samps, blinks)
    samps.loc[indices, mask_cols] = float('nan')
    samps['interpolated'] = 0
    samps.loc[indices, 'interpolated'] = 1
    return samps

def interpolate_blinks(samples, blinks, fields=['diameter']):
    '''Reconstructs Pupil Labs eye blinks with linear interpolation.
    
    Parameters
    ----------
    samples : pandas.DataFrame
        Must contain at least 'pupil_timestamp' and 'diameter' columns
    blinks : pandas.DataFrame
        Must contain 'start_timestamp' and 'end_timestamp' columns
    interp_cols : list, optional
        Columns to interpolate. The default is ['diameter'].
        
    Returns
    -------
    samps : pandas.DataFrame
        Blink-interpolated data
        
    '''
    #TODO: fix this pipeline
    samps = mask_blinks(samples, blinks, mask_cols=fields)
    n = samps[fields].isna().sum().max()
    samps = samps.interpolate(method='linear', axis=0, inplace=False)
    #breakpoint()
    print('{} samples ({:.3f} %) reconstructed with linear interpolation'.format(
        len(samps.loc[samps['interpolated']==1]), n))
    return samps

def mask_zeros(samples, mask_cols=['diameter']):
    '''Sets any 0 values in columns in mask_cols to NaN.
    
    Parameters
    ----------
    samples : pandas.DataFrame
        The samples to search for 0 values.
    mask_fields (list of strings)
        The columns to search for 0 values.
        
    '''
    samps = samples.copy(deep=True)
    for f in mask_cols:
        samps[samps[f] == 0] = float('nan')
    return samps

def interpolate_zeros(samples, fields=['diameter']):
    '''Replace 0s in "samples" with linearly interpolated data.
    
    Parameters
    ----------
    samples : pandas.DataFrame
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
    '''Applies a Butterworth filter to the given fields. 

    Parameters
    ----------
    samples : `pandas.DataFrame`
        DataFrame of samples containing the pupil data.
    fields : list, optional
        List of columns to be filtered. The default is ['diameter'].
    filt_order : int, optional
        Order of the filter. The default is 3.
    cutoff_freq : float
        Normalised cut-off frequency in hertz. For 4 Hz cut-off, this should 
        4/(sample_rate/2). The default is .01.
    inplace : bool, optional
        Whether to modify `samples` in place. The default is False.

    Returns
    -------
    samps : 
        The samples.

    '''
    samps = samples if inplace else samples.copy(deep=True)
    B, A = signal.butter(filt_order, cutoff_freq, output='BA')
    samps[fields] = samps[fields].apply(
        lambda x: signal.filtfilt(B, A, x), axis=0)
    return samps

def rolling_mean_series(samples,
                        window_size,
                        fields=['diameter'],
                        inplace=False):
    samps = samples if inplace else samples.copy(deep=True)
    for f in fields:
        samps[f] = samps[f].rolling(window_size).mean()
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
    samps = samples if inplace else samples.copy(deep=True)
    samps[fields] = samps[fields].apply(
        lambda x: signal.savgol_filter(x, window_length, filt_order), axis=0)
    return samps
