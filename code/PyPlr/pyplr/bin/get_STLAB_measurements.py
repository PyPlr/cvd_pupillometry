# -*- coding: utf-8 -*-
"""
Created on Thu May 28 13:51:20 2020

@author: engs2242
"""


import STLAB_apy as stlab


data_dir = r"C:\Users\engs2242\Documents\repos\cvd_pupillometry\data\led_spectra"

# colors for channels
colors = stlab.get_led_colors()

# set up device
device = stlab.setup_device(username='admin', identity=1, password='83e47941d9e930f6')

# turn off, if on
stlab.turn_off(device)

# leds to sample
leds = [0,1,2,3,4,5,6,7,8,9]

# collect samples
df = stlab.sample_leds(device, leds=leds, intensity=[4095], n_cycles=36, 
                     wait_between_cycles=300., wait_before_sample=.2)
df.reset_index(inplace=True)
df.to_csv("led_3h_35max_spec.csv")


#lkp = df.unstack(level=2)
#lkp.columns = [val[1] for val in lkp.columns]

#test = [67,3085,26,0,0,543,267,0,0,26]

#s = stlab.STLAB_predicted_spd(test, lkp_table=lkp)
