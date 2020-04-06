# -*- coding: utf-8 -*-
"""
Created on Sat Mar 28 11:06:05 2020

@author: engs2242
"""

from analysis_helpers import load_pupil, load_annotations, load_blinks, interpolate_blinks, butterworth_series, extract_events
import pandas as pd
import matplotlib.pyplot as plt

# recording directory
data_dir = "pipr_test/006/exports/000/"

# load data
samples = load_pupil(data_dir)
events  = load_annotations(data_dir)
blinks  = load_blinks(data_dir)

# pupil columns
pupil_cols = ["diameter","diameter_3d"]

# interpolate blinks
samples = interpolate_blinks(samples, blinks, interp_cols=pupil_cols)

# smooth - need to get right parameters
samples = butterworth_series(samples, fields=pupil_cols, filt_order=3, cutoff_freq=.05, inplace=False)
samples = samples[pupil_cols]

# extract events
events = events.query("label=='light_on'")
events.index = events["timestamp"]

ranges = extract_events(samples, events, offset=-600, duration=7200,
                   units="samples", borrow_attributes=["color"], return_count=False)
baselines = extract_events(samples, events, offset=-600, duration=600,
                   units="samples", borrow_attributes=["color"], return_count=False).mean(level=0)
ranges.diameter = (ranges.diameter / baselines.diameter - 1).values
ranges.diameter_3d = (ranges.diameter_3d / baselines.diameter_3d - 1).values

ranges.reset_index(inplace=True)
averages = ranges.groupby(["color","onset"], as_index=True).mean()

plt.plot(averages.loc["blue","diameter"], color='blue')
plt.plot(averages.loc["red","diameter"], color='red')


start = data.loc[0, 'pupil_timestamp']
data['pupil_timestamp'] = data['pupil_timestamp']-start
events['timestamp'] = events['timestamp'] - start
_, ax = plt.subplots(1,1,figsize=(12,4))
ax.plot(data["pupil_timestamp"],data["diameter_3d"])
for x1, x2 in zip(events.loc[events.label=='light_on',"timestamp"], events.loc[events.label=='light_off',"timestamp"]):
    print(x1, x2)
    plt.axvspan(x1,x2,color='black',alpha=.2)
    #plt.fill_betweenx(x1,x2,alpha=.2)

ax.set_xlabel('Time (s)')   
ax.set_ylabel('Pupil diameter (mm)') 
ax.set_ylim((2,8))  
ax.set_xlim((60,80))   
 
 
plt.savefig(data_dir + 'plr.png')

data.diameter_3d[7000:9000].plot()
