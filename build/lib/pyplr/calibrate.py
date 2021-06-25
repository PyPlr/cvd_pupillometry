#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
pyplr.calibrate
===============

Module to assist with calibrating the sphere. 

@author: jtm

'''

import os
import os.path as op
from time import sleep
from random import shuffle

import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import beta
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from pyplr.stlab import SpectraTuneLab, get_led_colors
from pyplr.CIE import get_CIE_1924_photopic_vl, get_CIES026


class SpectraTuneLabSampler(SpectraTuneLab):
    '''Subclass of `stlab.SpectraTuneLab` with added sampling methods.
    
    Optional support for concurrent measurements with external spectrometer. 
    
    '''
    
    def __init__(self, password, username='admin', identity=1, 
                 lighthub_ip='192.168.7.2', external=None):
        '''Initialize class and subclass. See `pyplr.stlab.SpectraTuneLab` for
        more info.
        
        Parameters
        ----------
        external : Class, optional
            Acquire concurrent measurements with an external spectrometer. 
            Must be a device class with ``.measurement(...)`` and 
            ``.wavelengths(...)`` methods. See `pyplr.oceanops.OceanOptics` 
            for an example.
            
        Returns
        -------
        None.

        '''
        super().__init__(password, username, identity, lighthub_ip)
        self.external = external
        self._ready_cache()

    def _ready_cache(self):
        self.stlab_spectra = []
        self.stlab_info = []
        if self.external:
            self.ex_spectra = []
            self.ex_info = []
    
    def make_dfs(self, save_csv=False):
        '''Turn cached data and info into pandas DataFrames and optionally 
        save to csv format.
        
        '''
        self.stlab_spectra = pd.DataFrame(self.stlab_spectra)
        self.stlab_spectra.columns = pd.Int64Index(self.wlbins)
        self.stlab_info = pd.DataFrame(self.stlab_info)
        if 'led' in self.stlab_info.columns:
            self.stlab_spectra['led'] = self.stlab_info['led']
            self.stlab_spectra['intensity'] = self.stlab_info['intensity']

        if self.external:
            self.ex_spectra = pd.DataFrame(self.ex_spectra)
            self.ex_spectra.columns = self.external.wavelengths()
            self.ex_info = pd.DataFrame(self.ex_info)
            if 'led' in self.ex_info.columns:
                self.ex_spectra['led'] = self.ex_info['led']
                self.ex_spectra['intensity'] = self.ex_info['intensity']
                
        if save_csv:
            self.stlab_spectra.to_csv(
                op.join(os.getcwd(), 'stlab_spectra.csv'))
            self.stlab_info.to_csv(
                op.join(os.getcwd(), 'stlab_info.csv'))            
            if self.ocean_optics:
                self.ex_spectra.to_csv(
                    op.join(os.getcwd(), 'external_spectra.csv'))            
                self.ex_info.to_csv(
                    op.join(os.getcwd(), 'external_info.csv'))            
        
    def full_readout(self, norm=False, setting={}):
        '''Get a full readout from STLAB.

        Parameters
        ----------
        norm : bool
            Whether to normalise the spectrum to the peak radiometric value.
        setting : dict, optional
            The current setting of the luminaire (if known), to be included in
            the `info_dict`. For example ``{'led' : 5, 'intensity' : 3000}``,
            or ``{'intensities' : [0, 0, 0, 300, 4000, 200, 0, 0, 0, 0]}``. 
            The default is ``{}``.

        Returns
        -------
        spec : np.array
            The spectrum.
        info_dict : dict
            Dictionary of information for spectrometer reading.

        '''
        tmps = self.get_pcb_temperature()
        ip   = self.get_input_power()
        it   = self.get_spectrometer_integration_time()
        dl   = self.get_dimming_level()
        rmv, spec = self.get_spectrometer_spectrum(norm=norm)
        info_dict = {
            'rmv': rmv,
            'LEDs_temp': tmps[0],
            'drivers_temp': tmps[1],
            'board_temp': tmps[2],
            'micro_temp': tmps[3],
            'integration_time': it,
            'input_power': ip,
            'dimming_level': dl
            }
        info_dict = {**info_dict, **setting}
        return spec, info_dict
    
    def sample(self, 
               leds=[0], 
               intensities=[500], 
               spectra=None,
               wait_before_sample=.3,
               ocean_optics=None,
               randomise=False):
        '''Sample a set of LEDs individually at a range of specified 
        intensities using STLABs on-board spectrometer. Alternatively, sample 
        a set of pre-defined spectra. Option to also obtain concurrent
        measurements with an external Ocean Optics spectrometer. Data are 
        stored in class lists.
    
        Parameters
        ----------
        leds : list, optional
            List of unique integers from 0-9 representing the LEDs to sample.
            The default is [0].
        intensities : list, optional
            List of integer values between 0-4095 representing the intensity 
            values at which to sample the LEDs. The default is [500].
        spectra : list, optinal
            List of predfined spectra to sample. Must be None if specifying
            leds or intensities. The default is None.
        wait_before_sample : float, optional
            Time in seconds to wait after setting a spectrum before acquiring 
            a measurement from the spectrometer(s). The default is .2.
        randomise : bool, optional
            Whether to randomise the order in which the LED-intensity settings 
            or spectra are sampled. The default is False.

    
        Returns
        -------
        None.
        
        '''
        if spectra and (leds or intensities):
            raise ValueError(
                'leds and intensities must be None when specifying spectra')
        
        # clear the cache
        self._ready_cache()

        # off spectrum    
        leds_off = [0]*10

        # turn stlab off if it's on
        self.set_spectrum_a(leds_off)
        
        # generate the settings
        if spectra:
            settings = spectra
            print('Sampling {} spectra: {}'.format(
                len(spectra), spectra))
        else:
            settings = [(l, i) for l in leds for i in intensities]
            print('Sampling {} leds at the following intensities: {}'.format(
                len(leds), intensities))
            
        # shuffle
        if randomise:
            shuffle(settings)
        
        # begin sampling            
        for i, s in enumerate(settings):
            if not spectra:
                led, intensity = s[0], s[1]
                setting = {'led': led, 'intensity': intensity}
                s = [0] * 10
                s[led] = intensity
                print('Measurement: {} / {}, LED: {}, intensity: {}'.format(
                    i + 1, len(settings), led, intensity))
            else:
                setting = {'intensities': s}
                print('Measurement: {} / {}, spectrum: {}'.format(
                    i + 1, len(settings), s))
                       
            # set the spectrum
            self.set_spectrum_a(s)
            sleep(wait_before_sample)
            
            # full readout from STLAB
            stlab_spec, stlab_info_dict = self.full_readout(setting=setting)
            self.stlab_spectra.append(stlab_spec)
            self.stlab_info.append(stlab_info_dict)
            
            if self.external:
                ex_spec, ex_info_dict = self.external.measurement(
                    setting=setting)
                self.ex_spectra.append(ex_spec)
                self.ex_info.append(ex_info_dict)
        
        # turn off
        self.turn_off()

# TODO: document this properly
class CalibrationContext:
    '''Create a calibration context based on spectrometer measurements. 
    
    Automatically creates a forward model of the device with linear
    interpolation. Currently this requires the measurements to be for each LED
    in steps of 65.
    
    Example
    -------
    >>> cc = CalibrationContext('spectrometer_data.csv')
    >>> fig = cc.plot_calibrated_spectra()
    
    '''
    def __init__(self, data, binwidth):
        '''

        Parameters
        ----------
        data : str
            Path to a csv file of calibrated spectrometer data. Must contain
            columns 'led' and 'intensity'.
        binwidth : int
            Binwidth of spectrometer data.

        Returns
        -------
        None.
            None.

        '''
        self.data = pd.read_csv(data, index_col=['led','intensity'])
        self.binwidth = binwidth
        self.wls = self.data.columns.astype('int')
        self.data.columns = self.wls
        self.lkp = self.create_lookup_table()
        self.aopic = self.create_alphaopic_irradiances_table()
        self.lux = self.create_lux_table()
        self.irradiance = self.lkp.sum(axis=1)
        self.curveparams = {}
    
    def plot_calibrated_spectra(self):
        '''Plot the calibrated spectra.

        Returns
        -------
        fig : Matplotlib.Figure
            The plot.

        '''
        # TODO: move to graphing?
        colors = get_led_colors(rgb=True)
        data = (self.data.reset_index()
                    .melt(id_vars=['led','intensity'], 
                          value_name='flux',
                          var_name='wavelength'))
        
        fig, ax = plt.subplots(figsize=(14,5))
        
        _ = sns.lineplot(x='wavelength', y='flux', data=data, hue='led',
                     palette=colors, units='intensity', ax=ax, 
                     lw=.1, estimator=None)
        ax.set_ylabel('SPD (W/m2/nm)')
        ax.set_xlabel('Wavelength (nm)')
        return fig    
    
    def create_lookup_table(self):
        '''Using `self.data`, create a lookup table for all settings with
        linear interpolation.

        Returns
        -------
        lkp_tbl : pd.DataFrame
            Interpolated data.

        '''
        #TODO: generalise and improve flexibility
        lkp_tbl = pd.DataFrame()
        for led, df in self.data.groupby(['led']):
            lkp_tbl = lkp_tbl.append(self.interp_led_spectra(led, df))
        lkp_tbl.set_index(['led','intensity'], inplace=True)
        return lkp_tbl
    
    def interp_led_spectra(self, led, df):
        intensities = df.index.get_level_values('intensity')
        minimum = intensities.min()
        maximum = intensities.max()
        new_intensities = np.linspace(
            minimum, maximum, maximum-minimum+1).astype('int')
        df = (df.droplevel(0)
                .reindex(new_intensities)
                .interpolate(method='linear'))
        df['intensity'] = df.index
        df['led'] = led
        return df
        
    def create_alphaopic_irradiances_table(self):
        '''Using the CIE026 spectral sensetivities, calculate alphaopic 
        irradiances (S, M, L, Rhod and Melanopic) for every spectrum in 
        `self.lkp`.
        
        Returns
        -------
        pd.DataFrame
            Alphaopic irradiances.

        '''
        sss = get_CIES026(asdf=True, binwidth=self.binwidth)
        sss = sss.fillna(0)
        return self.lkp.dot(sss)
    
    def create_lux_table(self):
        '''Using the CIE1924 photopic luminosity function, calculate lux for 
        every spectrum in `self.lkp`.

        Returns
        -------
        pd.DataFrame
            Lux values.

        '''
        vl = get_CIE_1924_photopic_vl(asdf=True, binwidth=self.binwidth)
        lux = self.lkp.dot(vl.values) * 683
        lux.columns = ['lux']
        return lux
    
    def fit_curves(self):
        '''Fit curves to the unweighted irradiance of spectral measurements
        and save the parameters.
        
        Returns
        -------
        fig
            Figure.

        '''
        # intensity levels from original data and corresponding irradiances
        idxs = self.data.index.get_level_values(1).unique().to_numpy()
        ir = self.irradiance.loc[:, idxs, :]
        
        # plot
        fig, axs = plt.subplots(2, 5, figsize=(16,6), sharex=True, sharey=True)
        axs = [item for sublist in axs for item in sublist]
        colors = get_led_colors()
        
        for idx, df in ir.groupby(level=0):
            xdata = idxs / 4095
            ydata = df.values
            ydata = ydata / np.max(ydata)
            
            # Curve fitting function
            def func(x, a, b):
                return beta.cdf(x, a, b)
        
            axs[idx].scatter(xdata, ydata, color=colors[idx], s=2)
            
            # Fit
            popt, pcov = curve_fit(beta.cdf, xdata, ydata, p0=[2.0, 1.0])
            self.curveparams[idx] = popt
            ypred = func(xdata, *popt)
            axs[idx].plot(xdata, ypred, color=colors[idx], 
                          label='fit: a=%5.3f, b=%5.3f' % tuple(popt))
            axs[idx].set_title('Channel {}'.format(idx))
            axs[idx].legend()
            
        for ax in [axs[0],axs[5]]:
            ax.set_ylabel('Output fraction (irradiance)')
        for ax in axs[5:]:
            ax.set_xlabel('Input fraction')   
            
        plt.tight_layout()
        
        return fig
    
    def optimise(self, led, intensities):
        '''Optimise a stimulus profile by applying the curve parameters. 

        Parameters
        ----------
        led : int
            LED being optimised.
        intensities : np.array
            Array of intensity values to optimise for specified LED.

        Returns
        -------
        np.array
            Optimised intensity values.

        '''
        if not self.curveparams:
            print('No parameters yet. Run .optimise(...) first...')
        params = self.curveparams[led]
        intensities = intensities / 4095
        return (beta.ppf(intensities, params[0], params[1]) * 4095).astype(
            'int')
    
    def predict_spd(self, intensities=[0,0,0,0,0,0,0,0,0,0], asdf=True):
        '''Using `self.lkp`, predict the spectral power distribution for a 
        given list of led intensities.
        
        Parameters
        ----------
        intensities : list
            List of intensity values for each led. The default is 
            ``[0,0,0,0,0,0,0,0,0,0]``.
        
        Returns
        -------
        spectrum : np.array
            Predicted spectrum for given intensities.
            
        '''
        spectrum = np.zeros(len(self.lkp.columns))
        for led, val in enumerate(intensities):
            spectrum += self.lkp.loc[(led, val)].to_numpy()
        if asdf:
            return pd.DataFrame(spectrum, index=self.wls).T
        else:
            return spectrum
        
    def match(self, match_led, match_led_intensity, 
              target_led, match_type='irrad'):
        '''Determine the appropriate intensity setting for `target_led` so that 
        its output will match `match_led` at `match_led_intensity` with respect 
        to `match_type`.

        Parameters
        ----------
        match_led : int
            The led to be matched.
        match_led_intensity : int
            The intensity of the led to be matched.
        target_led : int
            The led whose intensity is to be determined.
        match_type : str, optional
            The type of match to be performed. One of:
                
                * 'irrad' - overall (unweighted) irradiance
                * 'lux'   - lux
                * 'mel'   - melanopic irradiance
                * 'rhod'  - rhodopic irradiance
                * 's'     - s-cone-opic irradiance
                * 'm'     - m-cone-opic irradiance
                * 'l'     - l-cone-opic irradiance
                
            The default is 'irrad'.

        Returns
        -------
        error : float
            The absolute matching error.
        match_intensity : int
            The required intensity for `match_led`.

        '''
        if match_type=='irrad':
            values = self.irradiance
            target = values.loc[(match_led, match_led_intensity)]
        
        elif match_type=='lux':
            values = self.lux
            target = values.loc[(match_led, match_led_intensity)]
        
        elif match_type=='mel':
            values = self.aopic.Mel
            target = values.loc[(match_led, match_led_intensity)]
        
        elif match_type=='rhod':
            values = self.aopic.Rods
            target = values.loc[(match_led, match_led_intensity)]      
            
        elif match_type=='s':
            values = self.aopic.S
            target = values.loc[(match_led, match_led_intensity)]

        elif match_type=='m':
            values = self.aopic.M
            target = values.loc[(match_led, match_led_intensity)]
            
        elif match_type=='l':
            values = self.aopic.L
            target = values.loc[(match_led, match_led_intensity)]
            
        match_intensity = (values.loc[target_led]
                                 .sub(target)
                                 .abs()
                                 .idxmin())
        error = (values.loc[target_led]
                       .sub(target)
                       .abs()
                       .min())
        
        return error, match_intensity

         