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

class PLR:
    '''Class to handle data representing a pupil response to a flash of light.
    
    '''
    
    # TODO: add time stuff
    def __init__(self, plr, sample_rate, onset_idx, stim_duration):
        '''Initialise the PLR data.        

        Parameters
        ----------
        plr : arraylike
            Data representing a pupil response to a flash of light.
        sample_rate : int
            Frequency at which the data were sampled.
        onset_idx : int
            Ordinal index matching the onset of the light stimulus.
        stim_duration : int
            Duration of the light stimlus in seconds.

        Returns
        -------
        None.

        '''
        self.plr = plr
        self.sample_rate = sample_rate
        self.onset_idx = onset_idx
        self.stim_duration = stim_duration
        
    def velocity_profile(self):
        '''Return the velocity profile of the PLR. Assumes the samples are 
        evenly spaced, which is not the case with Pupil Labs data. Smoothing
        and averaging across multiple PLRs should remove cause for concern. 
    
        '''
        t = 1 / self.sample_rate
        return np.diff(self.plr, prepend=np.nan) / t
    
    def acceleration_profile(self):
        '''Return the acceleration profile of a PLR. Assumes the samples are 
        evenly spaced, which is not the case with Pupil Labs data. Smoothing
        and averaging across multiple PLRs should remove cause for concern. 
    
        '''
        t = 1 / self.sample_rate
        vel = self.velocity_profile()
        return np.diff(vel, prepend=np.nan) / t
    
    def baseline(self):
        '''Return the average pupil size between the start of s and onset_idx.
        
        '''
        return np.mean(self.plr[0:self.onset_idx])
    
    def pupil_size_at_onset(self):
        '''Return pupil size at stimulus onset.
    
        '''
        return self.plr[self.onset_idx]
    
    def latency_idx_a(self):
        '''Return the index where pupil size passes 1% change from size at 
        light  onset.
        
        '''
        b = self.pupil_size_at_onset()
        threshold = b - (b * .01)
        lidx = np.argmax(self.plr[self.onset_idx:] < threshold)
        lidx += self.onset_idx
        return lidx
    
    def latency_idx_b(self):
        '''Return the index of peak negative acceleration in the second after
        light onset.
    
        '''
        acc = self.acceleration_profile()
        lidx = np.argmin(acc[self.onset_idx:self.onset_idx + self.sample_rate])
        lidx += self.onset_idx
        return lidx  
    
    def latency_to_constriction_a(self):
        '''Return the time in miliseconds between stimulus onset and the first 
        sample where constriction exceeds a percentage of the baseline, using 
        the percent change threshold.
        
        '''
        lidx = self.latency_idx_a()
        return (lidx - self.onset_idx) * (1 / self.sample_rate)
    
    def latency_to_constriction_b(self):
        '''Return the time in miliseconds between stimulus onset and the time 
        at which the pupil reaches maximal negative acceleration within a 
        1-s window. See Bergamin & Kardon (2003) for justification. Requires 
        well-smoothed pupil data. 
        
        '''
        lidx = self.latency_idx_b()
        return (lidx - self.onset_idx) * (1 / self.sample_rate)
        
    def time_to_max_constriction(self):
        '''Return the time in miliseconds between stimulus onset and the peak 
        of pupil constriction.
        
        '''
        return np.argmin(self.plr[self.onset_idx:]) * (1 / self.sample_rate)
    
    
    def time_to_max_velocity(self):
        '''Return the time between stimulus onset and when pupil constriction 
        reaches maximum velocity.
        
        '''
        vel = self.velocity_profile()
        return np.argmin(vel[self.onset_idx:]) * (1 / self.sample_rate)
    
    def peak_constriction_idx(self):
        '''Return the index of the sample with peak constriction.
        
        '''
        return np.argmin(self.plr)
    
    def peak_constriction(self):
        '''Return the peak constriction value (i.e., the smallest pupil size).
        
        '''
        return np.min(self.plr)
    
    def constriction_amplitude(self):
        '''Return the constriction amplitude (i.e. the absolute difference 
        between baseline and peak constriction).
        
        '''
        peak = self.peak_constriction()
        base = self.baseline()
        return abs(peak - base)
    
    def average_constriction_velocity(self):
        '''Return the average constriction velocity.
    
        '''
        vel  = self.velocity_profile()
        lidx = self.latency_idx_a()
        pidx = self.peak_constriction_idx()
        return np.mean(abs(vel[lidx:pidx]))
        
    def max_constriction_velocity(self):
        '''Return the maximum constriction velocity.
        
        '''
        vel  = self.velocity_profile()
        pidx = self.peak_constriction_idx()
        return np.max(abs(vel[self.onset_idx:pidx]))
    
    def max_constriction_acceleration(self):
        '''Return the maximum constriction acceleration.
        
        '''
        acc  = self.acceleration_profile()
        pidx = self.peak_constriction_idx()
        return np.max(abs(acc[self.onset_idx:pidx]))
    
    def constriction_time(self):
        '''Return the time difference between constriction latency and peak 
        constriction.
        
        '''
        lat  = self.latency_to_constriction_a()
        ttmc = self.time_to_max_constriction()
        return  ttmc - lat
    
    def average_redilation_velocity(self):
        '''Return the average redilation velocity

        '''
        vel  = self.velocity_profile()
        pidx = self.peak_constriction_idx()
        return np.mean(abs(vel[pidx:])) 

        
    def max_redilation_velocity(self):
        '''Return the maximum redilation velocity.
        
        '''
        vel  = self.velocity_profile()
        pidx = self.peak_constriction_idx()
        return np.max(abs(vel[pidx:])) 
    
    def max_redilation_acceleration(self):
        '''Return the maximum redilation acceleration.
        
        '''   
        acc  = self.acceleration_profile()
        pidx = self.peak_constriction_idx()
        return np.max(abs(acc[pidx:]))
    
    def time_to_75pc_recovery(self):
        '''Return the time in ms until 75% recovery from baseline.
        
        '''
        base = self.baseline()
        pidx = self.peak_constriction_idx()
        amp  = self.constriction_amplitude()
        return np.argmax(
            self.plr[pidx:] > base - (amp / 4)) * (1 / self.sample_rate)
    
    def parameters(self):
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
            'Baseline': self.baseline(),
            'Latency_a': self.latency_to_constriction_a(),
            'Latency_b': self.latency_to_constriction_b(),
            'T2MaxVel': self.time_to_max_velocity(),
            'T2MaxCon': self.time_to_max_constriction(),
            'T2Rec75pc': self.time_to_75pc_recovery(),
            'PeakCon': self.peak_constriction(),
            'ConAmplitude': self.constriction_amplitude(),
            'VelConMax': self.max_constriction_velocity(),
            'VelConAve': self.average_constriction_velocity(),
            'AccConMax': self.max_constriction_acceleration(),
            'ConTime': self.constriction_time(),
            'VelRedAve': self.average_redilation_velocity(),
            'VelRedMax': self.max_redilation_velocity(),
            'AccRedMax': self.max_redilation_acceleration()
            }
        return pd.DataFrame.from_dict(
            params, orient='index', columns=['value'])
    
    def plot(self, vel=True, acc=True, print_params=True):
        '''Plot a PLR with option to add descriptive parameters and velocity / 
        acceleration profiles. 
        
        Parameters
        ----------
        vel_acc : bool, optional
            Whether to also plot the velocity and acceleration profiles.
            The default is False.
        print_params : bool, optional
            Whether to annotate the axis with the results of a call to 
            ``.parameters(...)``. The default is True.
            
        Returns
        -------
        fig : matplotlib.figure.Figure
            The plot.
            
        '''
        t_max = len(self.plr) / self.sample_rate
        time = np.linspace(
            0, t_max, num=len(self.plr)) - (self.onset_idx / self.sample_rate)
        b = self.baseline()
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(time, self.plr, lw=4)
        ax.axhline(b, 0, 1, ls='dashed', color='k', lw=1)
        ax.axvspan(0, 0 + self.stim_duration, color='k', alpha=.3)
        ax.set_ylabel('Pupil Size')
        ax.set_xlabel('Time (s)')
        
        if vel or acc:
            ax2 = ax.twinx()
            if vel:
                vel = self.velocity_profile()
                ax2.plot(time, vel, color='g', lw=2.5)
            if acc:
                acc = self.acceleration_profile()
                ax2.plot(time, acc, color='r', lw=1)
            ax2.set_ylabel('Velocity / Acceleration')
        
        if print_params:
            params = self.parameters()
            params = params.round(3)
            ax.text(.78, .03, params.to_string(
                header=False, justify='right'), size=8, transform=ax.transAxes)
                
        return fig

# TODO: is this worth it? 
class PIPR(PLR):
    def __init__(self, plr, sample_rate, onset_idx, stim_duration, other_plr=None):
        super().__init__(plr, sample_rate, onset_idx, stim_duration)
        self.other_plr = other_plr
        

# def pipr_amplitude(plr, sample_rate, window):
#     return plr[window[0]:window[1]].mean()
 
# def pipr_duration(plr, sample_rate, onset_idx, duration):
#     '''
#     Return the time to return to baseline after light offset. ISI should be 
#     between 100 and 660 s to allow pupil to return to baseline (see Adhikari
#     et al., 2015)
#     '''
#     offset_idx = onset_idx + duration
#     base = baseline(plr, onset_idx)
#     return np.argmax(plr[offset_idx:] >= base) * (1000 / sample_rate)

# def pipr_AUC_early(plr, sample_rate, onset_idx, duration):
#     '''
#     Unitless - AUC between offset and 10 s post offset
#     '''
#     base = baseline(plr, onset_idx)
#     offset_idx = onset_idx + duration
#     auc_idx = offset_idx + (sample_rate * 10)
#     return np.sum(base - abs(plr[offset_idx:auc_idx]))

# def pipr_AUC_late(plr, sample_rate, onset_idx, duration):
#     '''
#     Unitless - AUC between 10-30 s post offset
#     '''
#     base = baseline(plr, onset_idx)
#     offset_idx = onset_idx + duration
#     auc_idx = offset_idx + (sample_rate * 10)
#     return np.sum(base - abs(plr[auc_idx:auc_idx + (sample_rate * 30)]))
    
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