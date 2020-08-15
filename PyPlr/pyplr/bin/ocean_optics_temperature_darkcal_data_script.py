#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 10 10:27:12 2020

@author: jtm
"""
from time import sleep

import numpy as np
import pandas as pd
from seabreeze.spectrometers import Spectrometer

from oceanops import dark_measurement


def darkcal(spectrometer, integration_times=[1000]):
    
    wls = oo.wavelengths()
    data = pd.DataFrame()
    for it in integration_times:
        oo.integration_time_micros(it)
        sleep(.2)
        temps = oo.f.temperature.temperature_get_all()
        sleep(.2)
        board_temp = np.round(temps[0], decimals=2)
        micro_temp = np.round(temps[2], decimals=2)
        print('Board temp: {}, integration time: {}'.format(board_temp, it))
        intensities = pd.DataFrame(oo.intensities())
        intensities.rename(columns={0:'raw'}, inplace=True)
        data = pd.concat([data, intensities])

        
    midx = pd.MultiIndex.from_product(
        [[board_temp], [micro_temp], integration_times, wls],
        names=['board_temp', 'micro_temp', 'integration_time', 'wavelengths'])
    data.index = midx
    
    return data

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
data.to_csv('ocean_optics_temperature_darkcal_6-45degC.csv')


