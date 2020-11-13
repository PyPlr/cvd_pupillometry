#!/usr/bin/env python
# coding: utf-8

# In[4]:


import sys
sys.path.insert(0, '../../../PyPlr')

import numpy as np
import pandas as pd

from pyplr.CIE import get_CIES026


# # Spectral sensitivities

# In[5]:


_ , sss = get_CIES026(asdf=True)
#sss = sss[::5] # downsample to 5nm bins
sss.plot()


# # Spectral mesurements (STLAB)

# In[18]:


stlspec = pd.read_csv('/Users/jtm/OneDrive - Nexus365/spectrometer_data/stlab_led_intensity_spectra_08-17-20-14-31.csv')
stlspec


# In[19]:


stlinfo = pd.read_csv('/Users/jtm/OneDrive - Nexus365/spectrometer_data/stlab_led_intensity_info_08-17-20-14-31.csv')
stlinfo


# # Spectral mesurements (Ocean Optics)

# In[20]:


oospec = pd.read_csv('/Users/jtm/OneDrive - Nexus365/spectrometer_data/oo_led_intensity_spectra_08-17-20-14-31.csv')
oospec


# In[21]:


ooinfo = pd.read_csv('/Users/jtm/OneDrive - Nexus365/spectrometer_data/oo_led_intensity_info_08-17-20-14-31.csv')
ooinfo

