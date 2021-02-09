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
from time import sleep

import numpy as np
import pandas as pd

from pyplr import stlab
from pyplr.pupil import new_trigger, PupilCore, LightStamper, PupilGrabber
from pyplr.analysis import butterworth_series
from pyplr.plr import plr_metrics, plot_plr

def main(subjid='000', baseline=2., duration=10, record=False, control=False):
    
    outdir = op.join(os.getcwd(), subjid)
    # check for output directory
    if not op.isdir(outdir):
        os.mkdir(outdir)
        
    # # set up pupil
    pupil = PupilCore()
    
    # # setup stlab
    stlab.pulse_protocol([1000]*10, 1000, '1s_pulse')
    d = stlab.STLAB(username='admin', identity=1, password='83e47941d9e930f6')
    d.load_video_file('1s_pulse.dsf')
    
    # # set up pupil trigger
    trigger = new_trigger('LIGHT_ON')
    
    if control:
        input("Press Enter to administer stimulus...")
        
    if record:
        pupil.command('R {}'.format(outdir))
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
        di = pgt.get('diameter_3d')
        ts = np.array(pgt.get('timestamp'))
        df = pd.DataFrame(di, index=ts)
        df.columns = ['diameter_3d']
        df = butterworth_series(
            df, filt_order=3, cutoff_freq=4/(120/2), fields=['diameter_3d'])
       
        # find the closest timestamp
        idx = (np.abs(ts - lst.timestamp)).argmin()
        #df = df.iloc[idx-240:idx+600]
        df.reset_index(inplace=True)
        plr_metrics(df.diameter_3d, 120, idx, 0.01).to_csv(
            op.join(outdir, 'plr_params.csv'));
        plot_plr(df.diameter_3d, 120, idx, 1, vel_acc=True).savefig(
            op.join(outdir, 'plr_plot.png'), bbox_inches='tight');

if __name__ == '__main__':    
    try:
        main()
    except KeyboardInterrupt:
        print('Killed by user')
        sys.exit(0)
        
        
        
        