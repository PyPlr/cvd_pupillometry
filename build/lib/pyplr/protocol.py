# -*- coding: utf-8 -*-
"""
Created on Thu Mar 18 09:51:25 2021

@author: engs2242
"""

import os
import os.path as op
from subprocess import Popen

import tkinter as tk
from tkinter import simpledialog

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

def open_folder(folder):
    Popen(r'explorer /select,{}'.format(folder))