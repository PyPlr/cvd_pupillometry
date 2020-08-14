# -*- coding: utf-8 -*-
'''
Created on Fri Aug 14 11:07:38 2020

@author: - JTM

A module to help with measurents for Ocean Optics spectrometers. 

'''

from time import sleep

def adaptive_measurement(spectrometer):
    '''
    For a given light source, use an adaptive procedure to find the integration 
    time which returns a spectrum whose maximum reported value in raw units is
    between 80-90% of the maximum intensity value for the device. Can take up
    to a maximum of ~3.5 mins for lower light levels, though this could be 
    reduced somewhat by optimising the algorithm.

    '''
    # initial parameters
    intgtlims = spectrometer.integration_time_micros_limits
    maximum_intensity = spectrometer.max_intensity
    lower_intgt = None
    upper_intgt = None
    lower_bound = maximum_intensity * .8
    upper_bound = maximum_intensity * .9
    
    # start with 1000 micros
    intgt = 1000.0 
    max_reported = 0
    
    # keep sampling with different integration times until the maximum reported
    # value is within 80-90% of the maximum intensity value for the device
    while max_reported < lower_bound or max_reported > upper_bound:
        
        # if the current integration time is greater than the upper 
        # limit, set it too the upper limit
        if intgt >= intgtlims[1]:
            intgt = intgtlims[1]
            
        # set the spectrometer integration time
        spectrometer.integration_time_micros(intgt)
        sleep(.05)
        
        # obtain temperature measurements
        temps = spectrometer.f.temperature.temperature_get_all()
        sleep(.05)
        
        # obtain intensity measurements
        oo_data = spectrometer.intensities()
        
        # get the maximum reported value
        max_reported = max(oo_data)
        print('\tIntegration time: {} ms --> maximum reported value: {}'.format(
            intgt / 1000, max_reported))
        
        # if the integration time has reached the upper limit for the spectrometer,
        # exit the while loop, having obtained the final measurement
        if intgt == intgtlims[1]:
            break
        
        # if the max_reported value is less than the lower_bound and the
        # upper_ingt is not yet known, update the lower_intgt and double intgt
        # ready for the next iteration
        elif max_reported < lower_bound and upper_intgt is None:
            lower_intgt = intgt
            intgt *= 2.0
        
        # if the max_reported value is greater than the upper_bound, update
        # the upper_intgt and subtract half of the difference between 
        # upper_intgt and lower_intgt from intgt ready for the next iteration
        elif max_reported > upper_bound:
            upper_intgt = intgt
            intgt -= (upper_intgt - lower_intgt) / 2 
            
        # if the max_reported value is less than the lower_bound and the value
        # of upper_intgt is known, update the lower_intgt and add half
        # of the difference between upper_intgt and lower_intgt to intgt ready 
        # for the next iteration
        elif max_reported < lower_bound and upper_intgt is not None:
            lower_intgt = intgt
            intgt += (upper_intgt - lower_intgt) / 2
    
    # return the final counts and dict of sample-related info
    return oo_data, {'board_temp'       : [temps[0]],
                     'micro_temp'       : [temps[2]],
                     'integration_time' : [intgt],
                     'model'            : [spectrometer.model]}
    