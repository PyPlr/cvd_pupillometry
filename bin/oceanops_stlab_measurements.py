# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
from random import randrange, shuffle

import pandas as pd
from seabreeze.spectrometers import Spectrometer

from pyplr import stlab
from pyplr.oceanops import oo_measurement
    
# connect to stlab and dfs to store data
d = stlab.SpectraTuneLab(username='admin', identity=1, password='83e47941d9e930f6')

# connect to ocean optics and dfs to store data
oo = Spectrometer.from_first_available()

#%%
# specify leds and intensities to sample
# its = pd.read_csv('../data/oo_led_intensity_info_08-17-20-14-31.csv', 
#                   index_col=['led','intensity'], usecols='integration_time')
# leds = [0,1,2,3,4,5,6,7,8,9]
# intensities = [i for i in range(0, 4096, 65)]
# settings = [(l, i) for l in leds for i in intensities]
# shuffle(settings)
# settings.insert(1, settings.pop(settings.index((7, 195)))) # this particular setting is very annoying
# stlab_spectra1, stlab_info1, oo_spectra1, oo_info1 = d.sample(leds=leds, 
#                                                               intensities=intensities, 
#                                                               ocean_optics=oo,
#                                                               randomise=True,
#                                                               save_output=True,
#                                                               settings_override=settings)

#%%
# specify 40 random spectra to sample
spectra = [[randrange(4095) for led in range(10)] for spectrum in range(40)]
stlab_spectra2, stlab_info2, oo_spectra2, oo_info2 = d.sample(leds=None, 
                                                          intensities=None, 
                                                          spectra=spectra, 
                                                          ocean_optics=oo,
                                                          randomise=True,
                                                          save_output=True)


