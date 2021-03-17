#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 15 08:41:23 2021

@author: jtm
"""

import pandas as pd

from pyplr.plr import PLR

data = pd.read_csv('/Users/jtm/OneDrive - Nexus365/plr_protocol_1/ideal_plr.csv')


plr = PLR(plr=data.diameter[0:2400], 
          sample_rate=120,
          onset_idx=600, 
          stim_duration=1)
plr.plot()
plr.parameters()
