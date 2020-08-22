# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
from random import randrange

from seabreeze.spectrometers import Spectrometer

import stlab
    
# connect to stlab and dfs to store data
d = stlab.STLAB(username='admin', identity=1, password='83e47941d9e930f6')

# connect to ocean optics and dfs to store data
oo = Spectrometer.from_first_available()

#%%
# specify leds and intensities to sample
leds = [0,1,2,3,4,5,6,7,8,9]
intensities = [i for i in range(0, 4096, 65)]
stlab_spectra1, stlab_info1, oo_spectra1, oo_info1 = d.sample(leds=leds, 
                                                               intensities=intensities, 
                                                               ocean_optics=oo,
                                                               randomise=True,
                                                               save_output=True)

# specify 40 random spectra to sample
spectra = [[randrange(4095) for led in range(10)] for spectrum in range(40)]
stlab_spectra2, stlab_info2, oo_spectra2, oo_info2 = d.sample(leds=None, 
                                                          intensities=None, 
                                                          spectra=spectra, 
                                                          ocean_optics=oo,
                                                          randomise=True,
                                                          save_output=True)
