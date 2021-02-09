#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 10 10:27:12 2020

@author: jtm
"""

import pandas as pd
from seabreeze.spectrometers import Spectrometer

from oceanops import dark_measurement

#%% make a df to hold data
# connect to OceanOptics spectrometer
oo = Spectrometer.from_first_available()
data = pd.DataFrame()
it = 10
integration_times = []
while it < oo.integration_time_micros_limits[1]:
    integration_times.append(it)
    it *= 2

#%% set desired temperature before running this cell
t = oo.f.temperature.temperature_get_all()[0]
cycle = 0
while t < 45.00:
    data = data.append(dark_measurement(oo, integration_times))
    data['cycle'] = cycle
    cycle += 1
    t = oo.f.temperature.temperature_get_all()[0]
    
#%% run once data for all desired temperatures have been collected
data.to_csv('ocean_optics_temperature_darkcal_2-45degC.csv')


