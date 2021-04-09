#!/usr/bin/env python
# coding: utf-8

'''
PIPR with STLAB
===============
'''

from time import sleep
import random
#import winsound

from pyplr.pupil import PupilCore
from pyplr.stlab import SpectraTuneLab
from pyplr.protocol import input_subject_id, subject_dir, open_folder

# make list of stims
stims = ['./stimuli/1s_blue.dsf', './stimuli/1s_red.dsf'] #* 3
random.shuffle(stims)

# set up subject and recording
#subject_id = input_subject_id_gui()
subject_id = input_subject_id()
subj_dir = subject_dir(subject_id)

# Parameters for a 1s beep to notify impending stimulus
#alert_frequency = 466  # b flat
#alert_duration = 200  # 1 s

# Parameters for beep to say you can relax for a bit
#rest_frequency = 300  # b flat
#rest_duration = 1000  # 1 s  

# connect to Pupil Core
p = PupilCore()

# connect to stlab
d = SpectraTuneLab(password='83e47941d9e930f6', lighthub_ip='192.168.1.2')

# start recording
p.command('R {}'.format(subj_dir))

# wait a few seconds
sleep(5.)    

# loop over the list of stims
for i, stim in enumerate(stims):
    print(i, stim)
    # load video file and create trigger with metadata
    vf = d.load_video_file(stim)
    annotation = {**p.new_annotation('LIGHT_ON'), **vf['metadata']}
    
    # check the model fitting
    #p.check_3d_model(eyes=[0,1], alert=True)
    #sleep(2)
    print('\a')
    # notification of stimulus in 5 - 10 s
    #winsound.Beep(alert_frequency, alert_duration)

    # baseline of 5 - 10 s
    sleep(random.randrange(5000, 10001, 1) / 1000)
    
    # set up and start the LightStamper thread 
    lst_future = p.light_stamper(
        threshold=15, annotation=annotation, timeout=6)
    
    # wait 200 ms
    sleep(.2)
    
    # play the video file
    d.play_video_file()
    sleep(60.)
    
    # notification of stimulus in 5 - 10 s
    #winsound.Beep(rest_frequency, rest_duration)
    print('\a')
    
    if (i+1) < len(stims):
        sleep(60.)

# finish recording
sleep(5.)   
p.command('r')
