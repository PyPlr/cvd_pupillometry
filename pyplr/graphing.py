#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Created on Wed Dec 16 14:12:12 2020

@author: jtm
'''

import matplotlib.pyplot as plt


def pupil_preprocessing(nrows, subject, **kwargs):
    f, axs = plt.subplots(nrows=nrows, ncols=1, sharex=True, figsize=(14,14))
    for ax in axs:
        ax.set_ylabel('Pupil diameter')    
        ax.set_xlabel('Pupil timestamp')
    axs[0].legend(loc='upper right', labels=['pixels','mm'])
    f.suptitle('Preprocessing for subject: {}' .format(subject))
    return f, axs


