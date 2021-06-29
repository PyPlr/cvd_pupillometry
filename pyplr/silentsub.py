#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
pyplr.silentsub
===============

Module to assist with performing silent substitution for STLAB.

@author: jtm, ms

'''

import numpy as np


def smlri_calculator(x, d):
    """
    x is 20 values, between 0 and 1
    Takes 20 values, corresponding to the values for the primaries in two scenarios. Scenario 1: low-mel, scenario: high-mel.
    x[0:9] -> low-mel
    x[10:19] -> high-mel
    """
    settings1 = x[0:9]
    settings2 = x[10:19]
    smlr1 = 0
    smlr2 = 0
    for ii in range(0, 9):
        idx1 = int(np.round(settings1[ii] * 4095))
        idx2 = int(np.round(settings2[ii] * 4095))
        smlr1 = smlr1 + d.loc[(ii, idx1)]
        smlr2 = smlr2 + d.loc[(ii, idx2)]
    return smlr1, smlr2

def melanopsin_contrast_calculator(x, d):
    smlr1, smlr2 = smlri_calculator(x, d)
    contrast = 1-pow((smlr2.Mel-smlr1.Mel)/smlr1.Mel, 2)
    return contrast

def cone_contrast_calculator(x, d):
    smlr1, smlr2 = smlri_calculator(x, d)
    contrast = (np.array([(smlr2.S-smlr1.S)/smlr1.S, 
                         (smlr2.M-smlr1.M)/smlr1.M, 
                         (smlr2.L-smlr1.L)/smlr1.L]))
    return contrast