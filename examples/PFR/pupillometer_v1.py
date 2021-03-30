# -*- coding: utf-8 -*-
'''
Script for measuring the pupil flash response. 
==============================================

'''

import sys
import os.path as op
from time import sleep
import winsound

import numpy as np

from pyplr.protocol import (input_subject_id_gui, 
                            subject_dir, 
                            record_dir)
                            
from pyplr.stlab import SpectraTuneLab
from pyplr.pupil import PupilCore
from pyplr.utils import unpack_data_pandas
from pyplr.preproc import butterworth_series
from pyplr.plr import PLR

def main(subject_id='000', 
         baseline=1., 
         duration=8.,
         sample_rate=120,
         stimulus='./stimuli/PLR-3000-180-mw.dsf',
         record=True, 
         control=False):
    
    # set up subject and recording
    if subject_id is None:
        subject_id = input_subject_id_gui()
    subj_dir = subject_dir(subject_id)
    rec_dir = record_dir(subj_dir)
        
    # set up pupil
    p = PupilCore()
    
    # setup stlab
    d = SpectraTuneLab(password='83e47941d9e930f6')
    d.load_video_file(stimulus)

    # # set up pupil trigger
    annotation = p.new_annotation('LIGHT_ON')
    
    if control:
        input("Press Enter to administer stimulus...")
        
    if record:
        p.command('R {}'.format(rec_dir))
        sleep(1.)
        
    # start LightStamper and PupilGrabber
    lst_future = p.light_stamper(annotation, threshold=15, timeout=6.)
    pgr_future = p.pupil_grabber(topic='pupil.1.3d', 
                                 seconds=duration+baseline+2)
    
    # baseline
    sleep(baseline)
    d.play_video_file()

    while lst_future.running() or pgr_future.running():
        print('Waiting for futures...')
        sleep(1)
    
    if record:
        p.command('r')
    
    if not lst_future.result()[0]:
        print('light was not detected. Ending program.')
        sys.exit(0)
    
    # finished
    winsound.Beep(400, 200)

    # retrieve and process pupil data
    data = unpack_data_pandas(pgr_future.result())
    data = butterworth_series(
        data, 
        filt_order=3, 
        cutoff_freq=4/(sample_rate/2), 
        fields=['diameter_3d'])
    
    # lightstamper timestamp
    ts = lst_future.result()[1]
    
    # find the closest timestamp in the pupil data
    idx = (np.abs(ts - data.index)).argmin()
    
    start = int(idx-(baseline*sample_rate))
    end = int(idx+(duration*sample_rate))
    data = data.iloc[start:end]
    data.reset_index(inplace=True)

    plr = PLR(plr=data.diameter_3d.to_numpy(),
              sample_rate=sample_rate, 
              onset_idx=idx,
              stim_duration=1)
    plr.parameters().to_csv(op.join(rec_dir, 'plr_parameters.csv'))
    plr.plot().savefig(op.join(rec_dir, 'plr_plot.png'), bbox_inches='tight')
    data.to_csv(op.join(rec_dir, 'raw_data.csv'))
    
             
if __name__ == '__main__':    
    try:
        main()
    except KeyboardInterrupt:
        print('Killed by user')
        sys.exit(0)
        