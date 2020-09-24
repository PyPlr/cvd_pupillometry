#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 17 16:51:10 2020

@author: jtm
"""

import numpy as np
import pandas as pd
import spectres
from oceanops import predict_dark_spds

#c = pd.read_table('oo_dark_cal.txt', skiprows=2, sep='\t', index_col=False)

    


s = pd.read_csv('../oo_led_intensity_spectra_08-17-20-14-31.csv')
info = pd.read_csv('../oo_led_intensity_info_08-17-20-14-31.csv')

dark_spd = predict_dark_spds(info, 'oo_dark_cal.txt')

    
cal_per_wl = pd.read_csv('/Users/jtm/Documents/cvd_pupillometry/data/oceanoptics/oo_calibration.csv', header=None)
sensor_area_cm2 = pd.read_csv('/Users/jtm/Documents/cvd_pupillometry/data/oceanoptics/oo_sensorArea.csv', header=None)

cal_per_wl.index = s.columns
dark_spd.columns = s.columns
uj_per_pixel = (s - dark_spd) * cal_per_wl.T.values[0]
nm_per_pixel = np.median(np.diff(uj_per_pixel.columns.to_numpy(dtype='float')))
uj_per_nm = uj_per_pixel / nm_per_pixel
uj_per_cm2_per_nm = uj_per_nm / sensor_area_cm2.loc[0, 0]
uw_per_cm2_per_nm = uj_per_cm2_per_nm.div(info.integration_time, axis='rows')
# # Resample
uw_per_cm2_per_nm = spectres.spectres(np.arange(380, 781), s.columns.to_numpy(dtype='float'), uw_per_cm2_per_nm.to_numpy())
uw_per_cm2_per_nm = np.where(uw_per_cm2_per_nm < 0, 0, uw_per_cm2_per_nm)
w_per_m2_per_nm = pd.DataFrame(uw_per_cm2_per_nm * 0.01)

#def calibrated_radiance(spectra, dark_spectra, cal_per_wl, sensor_area):
    