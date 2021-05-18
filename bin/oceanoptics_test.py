#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 19 10:44:43 2021

@author: jtm
"""
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d

from pyplr.oceanops import predict_dark_counts, calibrated_radiance

# Load data
oo_spectra      = pd.read_csv('../data/S2_oo_led_intensity_spectra.csv', index_col=['led','intensity'])
oo_info         = pd.read_csv('../data/S2_oo_led_intensity_info.csv', index_col=['led','intensity'])
cal_per_wl      = pd.read_csv('../data/oo_calibration.csv', header=None)
sensor_area_cm2 = pd.read_csv('../data/oo_sensorArea.csv', header=None)[0]

# load darkcal
darkcal = pd.read_table('../data/oo_dark_cal.txt', skiprows=2, index_col=False)


oo_spectra.reset_index(inplace=True, drop=True)
oo_info.reset_index(inplace=True)
oo_dark_counts = predict_dark_counts(oo_info, darkcal)
wperm2pernm    = calibrated_radiance(
    oo_spectra, 
    oo_info, 
    oo_dark_counts,
    cal_per_wl,
    sensor_area_cm2.values[0])











wperm2pernm

wls = oo_dark_counts.columns
new_wls = np.arange(380, 780, 1)


d = oo_dark_counts.to_numpy()

f = interp1d(wls, d, fill_value='extrapolate')

ynew = f(new_wls)



import pandas as pd
from pyplr.oceanops import predict_dark_counts, calibrated_radiance

# Load Ocean Optics data
oo_spectra_fname = '../data/S2_oo_led_intensity_spectra.csv'
oo_info_fname = '../data/S2_oo_led_intensity_info.csv'
oo_spectra = pd.read_csv(
    oo_spectra_fname, index_col=['led','intensity'])
oo_spectra.reset_index(drop=True, inplace=True)
oo_info = pd.read_csv(oo_info_fname)

# Load a file with parameters accounting for the relationship 
# between temperature and integration time. This was created by
# sampling the dark spectrum across a range of temperatures 
# and times and fitting the data in MATLAB.
darkcal = pd.read_table(
    '../data/oo_dark_cal.txt', skiprows=2, index_col=False)

# Predict the dark spectrum for the temperatures and
# integration times of our measurements
oo_dark_counts = predict_dark_counts(oo_info, darkcal)

# Load some spectrometer constants
cal_per_wl = pd.read_csv(
    '../data/oo_calibration.csv', header=None)
sensor_area_cm2 = pd.read_csv(
    '../data/oo_sensorArea.csv', header=None)[0]

# Calculate calibrated radiance
w_m2_nm = calibrated_radiance(
    oo_spectra, 
    oo_info, 
    oo_dark_counts,
    cal_per_wl, 
    sensor_area_cm2.values[0])

# Clean up
w_m2_nm['led'] = oo_info['led']
w_m2_nm['intensity'] = oo_info['intensity']
w_m2_nm.set_index(['led', 'intensity'], inplace=True)
w_m2_nm.sort_index(inplace=True)
w_m2_nm = w_m2_nm.interpolate(axis=1)
w_m2_nm.to_csv('../data/S2_new_test.csv')
w_m2_nm

from pyplr.calibrate import CalibrationContext

cc = CalibrationContext('../data/S2_new_test.csv', binwidth=1)
cc2 = CalibrationContext('../data/S2_corrected_oo_spectra.csv', binwidth=1)
