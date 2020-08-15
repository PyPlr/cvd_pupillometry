# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
from random import shuffle, randrange

import pandas as pd
from seabreeze.spectrometers import Spectrometer

import stlab
    
# connect to stlab and dfs to store data
d = stlab.STLAB(username='admin', identity=1, password='83e47941d9e930f6')

# connect to ocean optics and dfs to store data
oo = Spectrometer.from_first_available()

#%%
# generate settings for samples and randomise order
leds = [0,1,2,3,4,5,6,7,8,9]
intensities = [i for i in range(0, 4096, 65)]
settings = [(l, i) for l in leds for i in intensities]
shuffle(settings)

# collect samples
stlab_spectra, stlab_info, oo_spectra, oo_info = d.sample_leds(leds=leds, intensities=intensities,  ocean_optics=oo, randomise=True)

stlab_spectra.to_csv('stlab_spectra_14_08_2020.csv', index=False)
stlab_info.to_csv('stlab_spectra_14_08_2020_info.csv', index=False)

oo_spectra.to_csv('oo_spectra_14_08_2020.csv', index=False)
oo_info.to_csv('oo_spectra_14_08_2020_info.csv', index=False)

oo_midx = pd.MultiIndex.from_frame(oo_info[['led','intensity']])
oo_spectra.index = oo_midx
oo_spectra.sort_index(inplace=True)

stlab_midx = pd.MultiIndex.from_frame(stlab_info[['led','intensity']])
stlab_spectra.index = stlab_midx
stlab_spectra.sort_index(inplace=True)

#%% sample spectra

spectra = [[randrange(4095) for led in range(10)] for spectrum in range(40)]
stlab_spectra, stlab_info, oo_spectra, oo_info = d.sample_spectra(spectra, ocean_optics=oo, randomise=True)

stlab_spectra.to_csv('stlab_spectra_14_08_2020.csv', index=False)
stlab_info.to_csv('stlab_spectra_14_08_2020_info.csv', index=False)

oo_spectra.to_csv('oo_spectra_14_08_2020.csv', index=False)
oo_info.to_csv('oo_spectra_14_08_2020_info.csv', index=False)


stlab_info