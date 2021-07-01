#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
pyplr.silentsub
===============

Module to assist with performing silent substitution for STLAB.

@author: jtm, ms

'''

import numpy as np

#from pyplr.calibrate import CalibrationContext

# class SilentSubstitutionContext(CalibrationContext):
    
#     def _init_(self):
#         super().__init__(self, data, binwidth)    
    
    

def smlri_calculator(low_mel, high_mel, aopic):
    '''
    

    Parameters
    ----------
    low_mel : array like
        Intensity settings for the low-melanopsin condition.
    high_mel : array like
        Intensity settings for the high-melanopsin condition.
    aopic : pd.DataFrame
        Data from cc.aopic

    Returns
    -------
    smlr1 : TYPE
        DESCRIPTION.
    smlr2 : TYPE
        DESCRIPTION.

    '''

    smlr1 = 0
    smlr2 = 0
    for led in range(10):
        idx1 = int(np.round(low_mel[led] * 4095))
        idx2 = int(np.round(high_mel[led] * 4095))
        smlr1 = smlr1 + aopic.loc[(led, idx1)]
        smlr2 = smlr2 + aopic.loc[(led, idx2)]
    return smlr1, smlr2

def melanopsin_contrast_calculator(low_mel, high_mel, aopic):
    smlr1, smlr2 = smlri_calculator(low_mel, high_mel, aopic)
    contrast = 1-pow((smlr2.Mel-smlr1.Mel)/smlr1.Mel, 2)
    return contrast

def cone_contrast_calculator(low_mel, high_mel, aopic):
    smlr1, smlr2 = smlri_calculator(low_mel, high_mel, aopic)
    contrast = (np.array([(smlr2.S-smlr1.S)/smlr1.S, 
                         (smlr2.M-smlr1.M)/smlr1.M, 
                         (smlr2.L-smlr1.L)/smlr1.L]))
    return contrast