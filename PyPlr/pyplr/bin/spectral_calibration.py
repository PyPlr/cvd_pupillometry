#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 17 16:51:10 2020

@author: jtm
"""

import numpy as np
import pandas as pd
import spectres
from pyplr.oceanops import predict_dark_spds, calibrated_radiance

#c = pd.read_table('oo_dark_cal.txt', skiprows=2, sep='\t', index_col=False)

    


s = pd.read_csv('../data/oo_led_intensity_spectra_08-17-20-14-31.csv')
info = pd.read_csv('../data/oo_led_intensity_info_08-17-20-14-31.csv')

dark_spd = predict_dark_spds(info, '../data/oo_dark_cal.txt')

    
cal_per_wl = pd.read_csv('../data/oo_calibration.csv', header=None)
sensor_area_cm2 = pd.read_csv('../data/oo_sensorArea.csv', header=None)

d = calibrated_radiance(s, info, dark_spd, cal_per_wl, sensor_area_cm2)

