# -*- coding: utf-8 -*-
'''
Script for measuring the pupil flash response. 
==============================================

'''

import sys
import os
import os.path as op
from time import sleep

import numpy as np

from pyplr import stlab
from pyplr.pupil import PupilCore, unpack_data_pandas
from pyplr.pipeline import butterworth_series
from pyplr.plr import plr_parameters, plot_plr

def main(subjid='000', baseline=2., duration=5, record=False, control=False):
    
    outdir = op.join(os.getcwd(), subjid)
    # check for output directory
    if not op.isdir(outdir):
        os.mkdir(outdir)
        
    # # set up pupil
    p = PupilCore()
    
    # setup stlab
    d = stlab.SpectraTuneLab(username='admin', identity=1,
                             lighthub_ip='192.168.7.2', 
                             password='83e47941d9e930f6')
    d.load_video_file('./stimuli/PLR-3000-180-mw.dsf')

    # # set up pupil trigger
    annotation = p.new_annotation('LIGHT_ON')
    
    if control:
        input("Press Enter to administer stimulus...")
        
    if record:
        p.command('R {}'.format(outdir))
        sleep(1.)
        
    # start LightStamper and PupilGrabber
    lst_future = p.light_stamper(annotation, threshold=15, timeout=6.)
    pgr_future = p.pupil_grabber(topic='pupil.1.3d', 
                                 seconds=duration+baseline+2)
    
    # baseline
    sleep(baseline)
    d.play_video_file()
    sleep(duration)
    
    if record:
        p.command('r')
    
    if not lst_future.result()[0]:
        print('light was not detected. Ending program.')
        sys.exit(0)
        
    # retrieve and process pupil data
    data = unpack_data_pandas(pgr_future.result())
    data = butterworth_series(
        data, filt_order=3, cutoff_freq=4/(120/2), fields=['diameter_3d'])
    
    # lightstamper timestamp
    ts = lst_future.result()[1]
    
    # find the closest timestamp in the pupil data
    idx = (np.abs(ts - data.index)).argmin()
    
    data = data.iloc[idx-240:idx+600]
    data.reset_index(inplace=True)
    plr_parameters(data.diameter_3d, 120, idx, 0.01).to_csv(
        op.join(outdir, 'plr_params.csv'));
    plot_plr(data.diameter_3d, 120, idx, 1, vel_acc=True).savefig(
        op.join(outdir, 'plr_plot.png'), bbox_inches='tight');

if __name__ == '__main__':    
    try:
        main()
    except KeyboardInterrupt:
        print('Killed by user')
        sys.exit(0)
        