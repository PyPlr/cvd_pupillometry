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
import tkinter as tk
from tkinter import simpledialog

from pyplr.stlab import SpectraTuneLab
from pyplr.pupil import PupilCore
from pyplr.utils import unpack_data_pandas
from pyplr.preproc import butterworth_series
from pyplr.plr import PLR

def input_subject_id():
    subject_id = input('Please enter subject ID: ')
    return subject_id

def input_subject_id_gui():
    ROOT = tk.Tk()
    ROOT.withdraw()
    return simpledialog.askstring(title='PyPlr Protocol',
                                  prompt='Enter Subject ID: ')

def subject_dir(subject_id):
    subj_dir = op.join(os.getcwd(), subject_id)
    if not op.isdir(subj_dir):
        os.mkdir(subj_dir)
    return subj_dir

def new_record_id(subject_dir):
    recording_id = 0
    for base, dirs, files in os.walk(subject_dir):
        if str(recording_id).zfill(3) == op.basename(base):
            recording_id += 1
    return str(recording_id).zfill(3)

def record_dir(subj_dir):
    record_id = new_record_id(subj_dir)
    rec_dir = op.join(subj_dir, record_id)
    if not op.isdir(subj_dir):
        os.mkdir(subj_dir)
    if not op.isdir(rec_dir):
        os.mkdir(rec_dir)
    return rec_dir

def main(subject_id=None, 
         baseline=2., 
         duration=8.,
         sample_rate=120,
         record=True, 
         control=False,
         config=None):
    
    # set up subject and recording
    if subject_id is None:
        subject_id = input_subject_id_gui()
    subj_dir = subject_dir(subject_id)
    rec_dir = record_dir(subj_dir)
        
    # set up pupil
    p = PupilCore()
    
    # setup stlab
    d = SpectraTuneLab(password='83e47941d9e930f6')
    d.load_video_file('./stimuli/PLR-3000-180-mw.dsf')

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
    plr.parameters().to_csv(op.join(rec_dir, 'plr_parameters.csv'))
    plr.plot().savefig(op.join(rec_dir, 'plr_plot.png'), bbox_inches='tight')
    data.to_csv(op.join(rec_dir, 'raw_data.csv'))
                 
if __name__ == '__main__':    
    try:
        main()
    except KeyboardInterrupt:
        print('Killed by user')
        sys.exit(0)
        