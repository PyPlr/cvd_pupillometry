# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
from random import randrange, shuffle

import pandas as pd

from pyplr.calibrate import SpectraTuneLabSampler
from pyplr.stlab import SpectraTuneLab
from pyplr.oceanops import OceanOptics
    

oo = OceanOptics.from_first_available()
d = SpectraTuneLabSampler(
    username='admin', identity=1, password='83e47941d9e930f6', ocean_optics=oo)

#%%
# specify leds and intensities to sample
leds = [0,1,2,3,4,5,6,7,8,9]
intensities = [i for i in range(0, 4096, 65)]

settings = [(l, i) for l in leds for i in intensities]
shuffle(settings)
d.sample(leds=leds, 
         intensities=intensities, 
         ocean_optics=oo,
         randomise=True,
         settings_override=settings)
d.make_dfs(save_csv=True)
#%%
# specify 40 random spectra to sample
spectra = [[randrange(4095) for led in range(10)] for spectrum in range(40)]
d.sample(leds=None,
         intensities=None, 
         spectra=spectra,
         randomise=True)
d.make_dfs(save_csv=True)


