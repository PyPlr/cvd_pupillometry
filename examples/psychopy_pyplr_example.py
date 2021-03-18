#!/usr/bin/env python
# -*- coding: utf-8 -*-

# PsychoPy pupillometer with standard monitor
# requires pyglet=1.4.10 to avoid threading error

import sys
sys.path.insert(0, '../')
import os.path as op
from time import sleep

import numpy as np
from psychopy import core, visual

from pyplr.pupil import PupilCore
from pyplr.utils import unpack_data_pandas
from pyplr.preproc import butterworth_series
from pyplr.plr import PLR
from pyplr.protocol import input_subject_id_gui, subject_dir, open_folder

def main(subject_id=None, 
         baseline=2., 
         duration=8.,
         sample_rate=120,
         record=True,
         control=False):
    
    # set up subject and recording
    if subject_id is None:
        subject_id = input_subject_id_gui()
    subj_dir = subject_dir(subject_id)
        
    # set up pupil
    p = PupilCore()
    
    # setup windows and stims
    win = visual.Window(size=[1920, 1080], screen=1, color="black")
    white = visual.Rect(win, units='pix', size=(1920, 1080))
    white.color='white'
    black = visual.Rect(win, units='pix', size=(1920, 1080))
    black.color='black'

    # set up pupil trigger
    annotation = p.new_annotation('LIGHT_ON')
    
    if control:
        input("Press Enter to administer stimulus...")
        
    if record:
        p.command('R {}'.format(subj_dir))
        sleep(1.)
        
    # start LightStamper and PupilGrabber
    lst_future = p.light_stamper(annotation, threshold=15, timeout=6.)
    pgr_future = p.pupil_grabber(topic='pupil.1.3d', 
                                 seconds=duration+baseline+2)
    
    # baseline
    sleep(baseline)

    white.draw()
    win.flip()
    core.wait(1.0)
    black.draw()
    win.flip()

    while lst_future.running() or pgr_future.running():
        print('Waiting for futures...')
        core.wait(10.)

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
    
    start = int(idx-(baseline*sample_rate))
    end = int(idx+(duration*sample_rate))
    data = data.iloc[start:end]
    data.reset_index(inplace=True)

    plr = PLR(plr=data.diameter_3d.to_numpy(),
              sample_rate=120, 
              onset_idx=idx,
              stim_duration=1)
    plr.parameters().to_csv(op.join(subj_dir, 'plr_parameters.csv'))
    plr.plot().savefig(op.join(subj_dir, 'plr_plot.png'), bbox_inches='tight')
    data.to_csv(op.join(subj_dir, 'raw_data.csv'))
    
    # Close the window
    win.close()
     
    # Close PsychoPy
    core.quit()
    
    open_folder(subj_dir)
             
if __name__ == '__main__':    
    try:
        main()
    except KeyboardInterrupt:
        print('Killed by user')
        sys.exit(0)
        