# -*- coding: utf-8 -*-
"""
Created on Mon Jun  8 16:47:20 2020

@author: engs2242
"""

from pyplr import stlab
import pandas as pd
from time import sleep, time

device = stlab.SpectraTuneLab(username='admin', identity=1, lighthub_ip='192.168.1.3', password='83e47941d9e930f6')

leds = [0,1,2,3,4,5,6,7,8,9]
intensity = [4095]

start = time()
df = pd.DataFrame()
for t in range(0,185,5):
    print("{} minutes left...".format(180-t))
    spectra = stlab.sample_leds(device, leds=leds, intensity=intensity, wait_before_sample=.5)
    spectra["time"] = t
    df = df.append(spectra)
    sleep(300)
end = time()
df.to_csv("STLAB_3h_stability.csv")    
