#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug  4 17:07:10 2020
@author: jtm
"""

'''
This script aims to do essentially what a neuroptics pupillometer does - 
adminster a light flash and give an instant read out of the data and PLR
parameters. Works well, but plenty of scope for optimising. 
'''

import os
import os.path as op
import sys
sys.path.insert(0, '../../')
import argparse
from time import sleep

import numpy as np
import pandas as pd

from pyplr import stlab
from pyplr.pupil import new_trigger, PupilCore, LightStamper, PupilGrabber
from pyplr.plr import plr_metrics, plot_plr

# func to smooth the pupil data
def butterworth_series(samples,
                       filt_order=3,
                       cutoff_freq=.05,
                       inplace=False):
    '''
    Applies a butterworth filter to the given fields
    See documentation on scipy's butter method FMI.
    '''
    import scipy.signal as signal
    samps = samples if inplace else samples.copy(deep=True)
    B, A = signal.butter(filt_order, cutoff_freq, output='BA')
    samps = signal.filtfilt(B, A, samps)
    return pd.Series(samps)

def main(subjid='000', baseline=2., duration=10, record=False, control=False):

    # check for output directory
    home = op.expanduser('~')
    if not op.isdir(op.join(home, 'pyplr_pupillometer')):
        os.mkdir(op.join(home, 'pyplr_pupillometer'))
    rec_dir = op.join(home, 'pyplr_pupillometer', subjid)
    if not op.isdir(rec_dir):
        os.mkdir(rec_dir)
        
    # # set up pupil
    pupil = PupilCore()
    
    # # setup stlab
    stlab.make_video_pulse([100]*10, 1000, '1s_pulse')
    d = stlab.STLAB(username='admin', identity=1, password='83e47941d9e930f6')
    d.load_video_file('1s_pulse.dsf')
    
    # # set up pupil trigger
    trigger = new_trigger('LIGHT_ON')
    
    if control:
        input("Press Enter to administer stimulus...")
        
    if record:
        pupil.command('R {}'.format(rec_dir))
        sleep(1.)
        
    # start LightStamper and PupilGrabber
    lst = LightStamper(pupil, trigger, threshold=15, wait_time=5.)
    pgt = PupilGrabber(pupil, topic='pupil.1.3d', secs=duration+baseline)
    lst.start()
    pgt.start()
    
    # # baseline
    sleep(baseline)
    d.play_video_file()
    sleep(duration)
    
    if record:
        pupil.command('r')
        
    if not pgt.isAlive():
        # retrieve and process pupil data
        di = pd.Series(pgt.get('diameter_3d'))
        di = butterworth_series(di, filt_order=3, cutoff_freq=.05)
        ts = np.array(pgt.get('timestamp'))
        
        # find the closest timestamp
        idx = (np.abs(ts - lst.timestamp)).argmin()
        plr_metrics(di, 120, idx, 0.01).to_csv(op.join(rec_dir, 'plr_params.csv'));
        plot_plr(di, 120, idx, 1, vel_acc=True).savefig(
            op.join(rec_dir, 'plr_plot.png'), bbox_inches='tight');

# name guard        
if __name__ == '__main__':
    # create CLI parser
    parser = argparse.ArgumentParser(
        description=('Measure the pupil light reflex'
                     ' and get an instant read out of the results'),
        epilog='Hope that worked'
        )
    parser.add_argument(
        '-o',
        '--out',
        help='name of directory for saving output (e.g. the subject id)',
        default='000'
        )
    parser.add_argument(
        '-r',
        '--record',
        action='store_true',
        help='save a Pupil Labs recording (requires Pupil Capture to be running)'
        )
    parser.add_argument(
        '-c',
        '--control',
        action='store_true',
        help='wait for experimenter input'
        )
    parser.add_argument(
        '-b',
        '--baseline',
        help='duration of the prestimulus baseline in seconds',
        default=2.
        )    
    parser.add_argument(
        '-d',
        '--duration',
        help='duration of the recording in seconds',
        default=8.
        )    
    parser.add_argument(
        '-v',
        '--version', 
        action='version', 
        version='%(prog)s 0.1'
        )

    args = parser.parse_args() 
    
    try:
        main(subjid=args.out, record=args.record, control=args.control)
    except KeyboardInterrupt:
        print('Killed by user')
        sys.exit(0)
        