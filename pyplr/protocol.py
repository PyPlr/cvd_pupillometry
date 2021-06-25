# -*- coding: utf-8 -*-
'''
pyplr.plr
=========

Tools for designing pupillometry protocols.

@author: jtm

'''

import sys
if sys.platform.startswith('win'):
    from winsound import Beep
    import tkinter as tk
    from tkinter import simpledialog
    
import os
import os.path as op
from subprocess import Popen

def input_subject_id():
    return input('Please enter subject ID: ')

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
        if 'rec' + str(recording_id).zfill(3) == op.basename(base):
            recording_id += 1
    return 'rec' + str(recording_id).zfill(3)

def record_dir(subj_dir):
    record_id = new_record_id(subj_dir)
    rec_dir = op.join(subj_dir, record_id)
    if not op.isdir(subj_dir):
        os.mkdir(subj_dir)
    if not op.isdir(rec_dir):
        os.mkdir(rec_dir)
    return rec_dir

def open_folder(folder):
    Popen(r'explorer /select,{}'.format(folder))
    
def beep_sound():
    if sys.platform=='darwin':
        print('\a')
    elif sys.platform.startswith('win'):
        Beep(440, 200)
        
    