#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
pyplr.oceanops
==============

A module to help with measurents for Ocean Optics spectrometers. 

'''

from time import sleep

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from seabreeze.spectrometers import Spectrometer

class OceanOptics(Spectrometer):
    '''Device class for Ocean Optics spectrometer with user-defined methods.
    
    '''
    
    def _init_(self):
        super(Spectrometer, self).__init__()
    
    # User defined methods
    def measurement(self, integration_time=None, setting={}):
        '''Obtain a measurement with an Ocean Optics spectrometer.
        
        If `integration_time` is not specified, will use an adaptive procedure
        that avoids saturation by aiming for a maximum reported value of 
        80-90% of the maximum intensity value for the device. Can take up to a
        maximum of ~3.5 mins for lower light levels, though this could be 
        reduced somewhat by optimising the algorithm.
    
        Parameters
        ----------
        integration_time : int
            The integration time to use for the measurement. Leave as None to
            adaptively set the integration time based on spectral measurements.
        setting : dict, optional
             Current setting of the light source (if known), to be included in 
             the `info`. For example ``{'led' : 5, 'intensity' : 3000}``, or 
             ``{'intensities' : [0, 0, 0, 300, 4000, 200, 0, 0, 0, 0]}``. 
             The default is ``{}``.
    
        Returns
        -------
        counts : np.array
            Raw intensity counts from the Ocean Optics spectrometer.
        info : dict
            Companion info for measurement.
    
        '''
        if integration_time:
            # set the spectrometer integration time
            self.integration_time_micros(int(integration_time))
            sleep(.01)
            
            # obtain temperature measurements
            temps = self.f.temperature.temperature_get_all()
            sleep(.01)
            
            # obtain intensity measurements
            counts = self.intensities()
            
            # get the maximum reported value
            max_reported = max(counts)
            print('\tIntegration time: {} ms --> maximum value: {}'.format(
                integration_time / 1000, max_reported))
                
        else:    
            # initial parameters
            intgtlims = self.integration_time_micros_limits
            maximum_intensity = self.max_intensity
            lower_intgt = None
            upper_intgt = None
            lower_bound = maximum_intensity * .8
            upper_bound = maximum_intensity * .9
            
            # start with 1000 micros
            intgt = 1000.0 
            max_reported = 0
            
            # keep sampling with different integration times until the maximum
            # reported value is within 80-90% of the maximum intensity value
            # for the device
            while max_reported < lower_bound or max_reported > upper_bound:
                           
                # if current integration time is greater than the upper limit, 
                # set it too the upper limit
                if intgt >= intgtlims[1]:
                    intgt = intgtlims[1]
                    
                # set the spectrometer integration time
                self.integration_time_micros(intgt)
                sleep(.01)
                
                # obtain temperature measurements
                temps = self.f.temperature.temperature_get_all()
                sleep(.01)
                
                # obtain intensity measurements
                counts = self.intensities()
                
                # get the maximum reported value
                max_reported = max(counts)
                print('\tIntegration time: {} ms --> maximum value: {}'.format(
                    intgt / 1000, max_reported))
                
                # if the integration time has reached the upper limit for the 
                # spectrometer, exit the while loop, having obtained the final 
                # measurement
                if intgt == intgtlims[1]:
                    break
                
                # if the max_reported value is less than the lower_bound and 
                # the upper_ingt is not yet known, update the lower_intgt and 
                # double intgt ready for the next iteration
                elif max_reported < lower_bound and upper_intgt is None:
                    lower_intgt = intgt
                    intgt *= 2.0
                
                # if the max_reported value is greater than the upper_bound, 
                # update the upper_intgt and subtract half of the difference
                # between upper_intgt and lower_intgt from intgt ready for the
                # next iteration
                elif max_reported > upper_bound:
                    upper_intgt = intgt
                    intgt -= (upper_intgt - lower_intgt) / 2 
                    
                # if the max_reported value is less than the lower_bound and 
                # the value of upper_intgt is known, update the lower_intgt and
                # add half of the difference between upper_intgt and 
                # lower_intgt to intgt ready for the next iteration
                elif max_reported < lower_bound and upper_intgt is not None:
                    lower_intgt = intgt
                    intgt += (upper_intgt - lower_intgt) / 2
        
        info = {
            'board_temp': temps[0],
            'micro_temp': temps[2],
            'integration_time': intgt,
            'model': self.model
            }
        info = {**info, **setting}
        
        return counts, info    

    def dark_measurement(self, integration_times=[1000]):
        '''Sample the dark spectrum with a range of integration times. 
        
        Do this for a range of temperatures to map the relationship between 
        temperature and integration time.
        
        Parameters
        ----------
        integration_times : list, optional
            List of integers representing integration times in microseconds. 
            The default is [1000].

        Returns
        -------
        data : `pandas.DataFrame`
            Dark counts.
        info : `pandas.DataFrame`
            Companion info.

        '''
        data = []
        info = []
        for intgt in integration_times:
            self.integration_time_micros(intgt)
            sleep(.05)
            c, i = self.measurement(integration_time=intgt)
            print('Board temp: {}, integration time: {}'.format(
                i['board_temp'], intgt))
            data.append(c)
            info.append(i)
        data = pd.DataFrame(data, columns=self.wavelengths())   
        info = pd.DataFrame(info)
        return data, info

def predict_dark_counts(spectra_info, darkcal):
    '''Predict dark counts from temperature and integration times.
    
    These get subtracted from measured pixel counts in 
    `OceanOptics.calibrated_radiance(...)`

    Parameters
    ----------
    spectra_info : pd.DataFrame
        Spectra companion info containing the 'board_temp' and 
        'integration_time' variables.
    darkcal : `pandas.DataFrame`
        Parameters accounting for the relationship between PCB temperature and 
        integration time and their effect on raw pixel counts. Currently 
        generated in MATLAB. 

    Returns
    -------
    pandas.DataFrame
        The predicted dark counts.

    '''
    dark_counts = []
    
    for idx, row in spectra_info.iterrows():
        x  = spectra_info.loc[idx, 'board_temp']
        y  = spectra_info.loc[idx, 'integration_time']
        dark_spec = []
        
        for i in range(0, darkcal.shape[0]):
            p00 = darkcal.loc[i, 'p00']
            p10 = darkcal.loc[i, 'p10']
            p01 = darkcal.loc[i, 'p01']
            p20 = darkcal.loc[i, 'p20']
            p11 = darkcal.loc[i, 'p11']
            p30 = darkcal.loc[i, 'p30']
            p21 = darkcal.loc[i, 'p21']
            
            dark_spec.append(p00 
                             + p10*x 
                             + p01*y 
                             + p20*x*x 
                             + p11*x*y 
                             + p30*x*x*x 
                             + p21*x*x*y)

        dark_counts.append(dark_spec)
        
    # TODO: add code with function parameter to exclude poorly fitting pixels. 
    # using a visually determined threshold, for now. 
    FIT_RMSE_THRESHOLD = 110
    dark_counts = np.where(
        darkcal.rmse > FIT_RMSE_THRESHOLD, np.nan, dark_counts)
        
    return pd.DataFrame(dark_counts)

def calibrated_radiance(spectra, 
                        spectra_info, 
                        dark_counts, 
                        cal_per_wl, 
                        sensor_area):
    '''Convert raw OceanOptics data into calibrated radiance.
    
    Parameters
    ----------
    spectra : `pandas.DataFrame`
        Spectra to be calibrated, as returned by 
        `OceanOptics.measurement(...)`. Column index must be spectrometer
        wavelength bins. 
    spectra_info : `pandas.DataFrame`
        Spectra companion info, as returned by `OceanOptics.measurement(...)`.
    dark_counts : `pandas.DataFrame`
        Predicted dark counts for each pixel. See 
        `OceanOptics.predict_dark_counts(...)`
    cal_per_wl : `pandas.DataFrame`
        Spectrometer calibration file.
    sensor_area : float
        Sensor area in cm2. Spectrometer constant. 

    Returns
    -------
    w_per_m2_per_nm : `pandas.DataFrame`
        Calibrated radiance data in watts per meter squared units.

    '''
    # we have no saturated spectra due to adaptive measurement
    # convert integration time from us to s
    spectra_info['integration_time'] = (spectra_info['integration_time']
                                        / (1000*1000))
    # float index for spectra columns
    spectra.columns = pd.Float64Index(spectra.columns)
    
    # borrow wavelength indices
    cal_per_wl.index = spectra.columns
    dark_counts.columns = spectra.columns
    
    # microjoules per pixel
    uj_per_pixel = (spectra - dark_counts) * cal_per_wl.T.values[0]
    
    # get the wavelengths and calculate the nm/pixel binwidth
    wls = uj_per_pixel.columns
    nm_per_pixel = np.hstack(
        [(wls[1]-wls[0]), (wls[2:]-wls[:-2])/2, (wls[-1]-wls[-2])])
    
    # calculate microwatts per cm2 per nanometer
    uj_per_nm = uj_per_pixel / nm_per_pixel
    uj_per_cm2_per_nm = uj_per_nm / sensor_area
    uw_per_cm2_per_nm = uj_per_cm2_per_nm.div(
        spectra_info['integration_time'], axis='rows')
    
    # Resample to visible spectrum in 1 nm bins
    uw_per_cm2_per_nm = uw_per_cm2_per_nm.to_numpy()
    f = interp1d(wls, uw_per_cm2_per_nm, fill_value='extrapolate')
    new_wls = np.arange(380, 781, 1)
    uw_per_cm2_per_nm = f(new_wls)
    
    # old way used spectres
    # uw_per_cm2_per_nm = spectres.spectres(new_wls, spectra.columns.to_numpy(
    #         dtype='float'), uw_per_cm2_per_nm.to_numpy())
    
    uw_per_cm2_per_nm = np.where(uw_per_cm2_per_nm < 0, 0, uw_per_cm2_per_nm)
    w_per_m2_per_nm = pd.DataFrame(uw_per_cm2_per_nm * 0.01)
    w_per_m2_per_nm.columns = pd.Int64Index(new_wls)
    
    return w_per_m2_per_nm