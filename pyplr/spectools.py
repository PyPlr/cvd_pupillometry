#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 20 10:13:58 2021

@author: jtm
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pyplr.CIE import get_CIES026, get_CIE_CMF, get_CIE_1924_photopic_vl

  
def plot_spectrum(spectrum, color):
    bins = np.linspace(380,780,81)
    plt.plot(bins, spectrum, color=color)

def get_led_colors(rgb=False):
    if rgb:
        colors = [[.220, .004, .773, 1.], [.095, .232, .808, 1.],
                  [.098, .241, .822, 1.], [.114, .401, .755, 1.],
                  [.194, .792, .639, 1.], [.215, .895, .489, 1.],
                  [.599, .790, .125, 1.], [.980, .580, .005, 1.],
                  [.975, .181, .174, 1.], [.692, .117, .092, 1.]]
    else:
        colors = ['blueviolet', 'royalblue', 'darkblue',
              'blue', 'cyan', 'green', 'lime',
              'orange','red','darkred']
    return colors

def get_wlbins(bin_width=5):
    if bin_width==1:
        wlbins = [int(val) for val in np.linspace(380, 780, 81*bin_width)]
    else:
        wlbins = [int(val) for val in np.linspace(380, 780, 81)]
    return wlbins

def spec_to_xyz(spec, cmf):
    '''Convert a spectrum to an xyz point.

    The spectrum must be on the same grid of points as the colour-matching
    function, cmf: 380-780 nm in 5 nm steps.

    '''    
    XYZ = np.sum(spec[:, np.newaxis] * cmf, axis=0)
    den = np.sum(XYZ)
    if den == 0.:
        return XYZ
    return XYZ / den

def spectra_to_xyz(spectra, binwidth):
    '''
    Calculate the CIE 1931 xy chromaticity coordinates for a collection of
    spectra. The DataFrame must have columns (or multi index) with names

    Parameters
    ----------
    spectra : DataFrame
        As output by stlab.sample

    Returns
    -------
    xyz : DataFrame
        The xyz values for each spectrum.
        
    '''
    cmf = get_CIE_CMF(binwidth=binwidth)[1:].T
    idx = []    
    xyz = []
    for i, spec in spectra.groupby(by=['led','intensity']):
        idx.append(i)
        xyz.append(spec_to_xyz(spec.to_numpy()[0], cmf=cmf))
    xyz = pd.DataFrame(xyz, columns=['X','Y','Z'])
    xyz.index = pd.MultiIndex.from_tuples(idx, names=['led','intensity'])
    return xyz

def spectra_to_peak_wavelengths(spectra):
    '''Calculate the peak wavelengths for a given set of spectra.

    '''
    return spectra.idxmax(axis=1)

def spectra_to_dominant_wavelength(spectra, binwidth, 
                                   ref_white=[0.3333, 0.3333]):
    from colour.colorimetry.dominant import dominant_wavelength
    
    xyz = spectra_to_xyz(spectra, binwidth=binwidth)
    idx = []
    dwl = []
    for i, row in xyz.iterrows():
        result = dominant_wavelength((row.X, row.Y), ref_white)
        dwl.append(result[0])
        idx.append(i)
    dwl = pd.DataFrame(dwl, columns=['wavelength'])
    dwl.index = pd.MultiIndex.from_tuples(idx, names=['led','intensity'])
    return dwl

def spectra_to_melanopic_irradiance(spectra, binwidth):
    # get melanopsin sensitivity
    sss = get_CIES026(asdf=True, binwidt=binwidth)
    mel = sss['Mel']
    
    # aggregate to melanopic irradiance
    mi = spectra.groupby(by=['led','intensity'])['flux'].agg(
        lambda x: x.dot(mel.values.T))
    return mi

def spectra_to_luminance(spectra, grouper=['led','intensity']):
    
    # get luminancephotopic luminance curve
    vl = get_CIE_1924_photopic_vl(asdf=True)
    vl = vl[::5]
    
    # aggregate to luminance
    lum = spectra.groupby(by=grouper).agg(lambda x: x.dot(vl.values))
    return lum    

 
def explore_spectra(spectra, binwidth):
    '''
    This function takes a DataFrame of spectra and plots them, along with other
    useful info.
    '''
    from colour.plotting import plot_chromaticity_diagram_CIE1931
    import seaborn as sns
    
    # get xy chromaticities
    xyz = spectra_to_xyz(spectra, binwidth)
    
    # get peak wavelength
    pwl = spectra_to_peak_wavelengths(spectra)
    
    # get dominant wavelength
    dwl = spectra_to_dominant_wavelength(spectra, binwidth=binwidth)
    
    # get malanopic irradiances
    mi = spectra_to_melanopic_irradiance(spectra, binwidth=binwidth)

    # set up figure
    fig , ax = plt.subplots(10, 4, figsize=(16,36))
    colors = get_led_colors()
    long_spectra = spectra_wide_to_long(spectra)
    for i, led in enumerate(ax):
    
        # plot spectra
        sns.lineplot(x='wavelength', y='flux', data=long_spectra[long_spectra.led==i], color=colors[i], units='intensity',ax=ax[i, 0], lw=.1, estimator=None)
        ax[i, 0].set_ylim((0,3500))
        ax[i, 0].set_xlabel('Wavelength $\lambda$ (nm)')
        ax[i, 0].set_ylabel('Flux (mW)')
    
        # plot color coordinates
        plot_chromaticity_diagram_CIE1931(standalone=False, axes=ax[i, 1], title=False, show_spectral_locus=False)
        ax[i, 1].set_xlim((-.15,.9))
        ax[i, 1].set_ylim((-.1,1))
        ax[i, 1].scatter(xyz.loc[i,'X'], xyz.loc[i,'Y'], c='k', s=3)
        
        # plot peak and dominant wavelength as a function of input
        inpt = long_spectra['intensity'] / 4095
        inpt = np.linspace(0, 1, len(long_spectra.intensity.unique()))
        ax[i, 2].plot(inpt, pwl.loc[i, 'wavelength'], color=colors[i], lw=1, label='Peak')
        ax[i, 2].set_xlabel('Input')
        
        ax[i, 2].plot(inpt, dwl.loc[i, 'wavelength'], color=colors[i], lw=3, label='Dominant')
        ax[i, 2].set_xlabel('Input')
        ax[i, 2].set_ylabel('$\lambda$ (nm)')
        low  = dwl.loc[i, 'wavelength'].min()-dwl.loc[i, 'wavelength'].min()*0.1
        high = dwl.loc[i, 'wavelength'].max()+dwl.loc[i, 'wavelength'].max()*0.1
        ax[i, 2].set_ylim((low, high))
        ax[i, 2].legend()
        
        # plot melanopic irradience
        ax[i, 3].plot(inpt, mi.loc[i], color=colors[i])
        ax[i, 3].set_ylim((0,14000))
        ax[i, 3].set_xlabel('Input')
        ax[i, 3].set_ylabel('Melanopic irradiance (mW)')
    
    return fig    

def spectra_wide_to_long(wide_spectra):
    return (wide_spectra.reset_index()
                        .melt(id_vars=['led','intensity'], 
                              var_name='wavelength', value_name='flux')
                        .sort_values(by=['led','intensity'])
                        .reset_index(drop=True))
