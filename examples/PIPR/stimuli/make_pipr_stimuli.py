# -*- coding: utf-8 -*-

'''
PIPR with STLAB
===============

@author: jtm
'''
import matplotlib.pyplot as plt
import seaborn as sns

from pyplr.CIE import get_CIES026
from pyplr.calibrate import CalibrationContext
from pyplr import stlab

sns.set_context('paper', font_scale=2)
sns.set_style('whitegrid')

cc = CalibrationContext(
    '../../../data/S2_corrected_oo_spectra.csv', binwidth=1)

blue_led = 3
red_led = 9
target_lux = 800

# find the required intensity setting of the blue led for 800 lux
blue_intensity = (cc.lux.loc[blue_led].sub(target_lux)
                                      .abs()
                                      .idxmin()
                                      .values[0])

# find the intensity setting of the red led for 800 lux
red_intensity = cc.match(match_led=blue_led, 
                         match_led_intensity=blue_intensity, 
                         target_led=red_led, 
                         match_type='irrad')[1]

# plot stims
fig, ax = plt.subplots(figsize=(6,4))
sss = get_CIES026(asdf=True, binwidth=1)
ax.plot(cc.lkp.loc[(blue_led, blue_intensity)], c='blue')
ax.plot(cc.lkp.loc[(red_led, red_intensity)], c='red')
    
ax2 = ax.twinx()
ax2.plot(sss['Mel'], ls='dashed', c='steelblue')
ax2.set_ylabel('Melanopsin spectral sensitivity', c='steelblue')
ax.set_xlabel('Wavelength (nm)')
ax.set_ylabel('W/m$^2$/nm');
fig.savefig('./pipr_stims.svg', bbox_inches='tight')

# make video files
blue_spec, red_spec = [0]*10, [0]*10
blue_spec[blue_led] = blue_intensity
red_spec[red_led] = red_intensity

stlab.pulse_protocol(pulse_spec=blue_spec,
                     pulse_duration=1000, 
                     fname='1s_blue',
                     metadata={'color':'blue'})
stlab.pulse_protocol(pulse_spec=red_spec, 
                     pulse_duration=1000, 
                     fname='1s_red',
                     metadata={'color':'red'})