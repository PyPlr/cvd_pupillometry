#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
pyplr.extract
=============

'''
from copy import deepcopy

import numpy as np
import pandas as pd

#TODO: optimse and debug
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
        The samples from which to extract events. Index must be timestamp.
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
    breakpoint()    
    # get the list of start time indices
    event_starts = events.index.to_series()

    # find the indexes of the event starts, and offset by sample count
    range_idxs = np.searchsorted(
        samples.index, event_starts.iloc[:], 'left') + offset
    range_duration = duration
    
    # make a hierarchical index
    samples['orig_idx'] = samples.index
    midx = pd.MultiIndex.from_product(
        [list(range(len(event_starts))), list(range(range_duration))],
        names=['event', 'onset'])
    
    # get the samples
    df = pd.DataFrame()
    idx = 0
    for start_idx in range_idxs:
        # get the start time and add the required number of indices
        end_idx = start_idx + range_duration - 1  # pandas.loc indexing is inclusive
        # deepcopy for old bugs
        new_df = deepcopy(
            samples.loc[samples.index[start_idx] : samples.index[end_idx]])
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
    reject_idxs = (pct_interp.loc[pct_interp['interpolated'] > interp_thresh]
                             .index.to_list())
    ranges['reject'] = 0
    if reject_idxs:
        ranges.loc[reject_idxs, 'reject'] = 1
    if drop:
        ranges = ranges.drop(index=reject_idxs)
        print('{} trials were dropped from the DataFrame'.format(
            len(reject_idxs)))
    else:
        print('{} trials were marked for rejection'.format(len(reject_idxs)))
    return ranges
