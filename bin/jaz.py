#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  4 09:31:36 2022

@author: jtm545
"""

from random import randrange, shuffle

import matplotlib.pyplot as plt
import pandas as pd

from pyplr.calibrate import SpectraTuneLabSampler
from pyplr.stlab import SpectraTuneLab
from pyplr.oceanops import OceanOptics

# Load calibration file for lamp with raw fiber
lamp_cal_fname = '/Users/jtm545/Projects/BakerWadeBBSRC/hardware/OceanOptics/HL-2000/030410313_CC.LMP'
lamp_cal = pd.read_csv(lamp_cal_fname, sep='\t', header=None)
lamp_cal.plot(x=0, y=1)

# Connect to spectrometer
jaz = OceanOptics.from_serial_number('JAZA1505')
#usb2k = OceanOptics.from_serial_number('USB2G15413')

# Obtain measurement and plot
wls, spd = jaz.spectrum(correct_dark_counts=(True), 
                        correct_nonlinearity=(True))
plt.plot(wls, spd)

# Obtain measurement with adaptive integration time
spd, info = jaz.measurement()
plt.plot(wls, spd)

from scipy.interpolate import interp1d

lamp_cal = lamp_cal.set_index(0)
f = interp1d(lamp_cal.index.to_numpy(), lamp_cal[1].to_numpy())
new = f(wls)
