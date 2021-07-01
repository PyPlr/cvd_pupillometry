#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
pyplr.jeti
==========

A (currently) bare bones serial interface for JETI Spectraval. 

@author: jtm
'''

import numpy as np
import serial

class Spectraval:
    
    def _init_(self, 
               port='/dev/cu.usbserial-DJ5F3W9U', 
               baudrate=921600, 
               bytesize=8, 
               stopbits=1, 
               parity='N', 
               timeout=240):

        
        # open serial connection
        self.ser = serial.Serial(
            port = port,
            baudrate = baudrate, 
            bytesize = bytesize, 
            stopbits = stopbits, 
            parity = parity,
            timeout = timeout)
        
    def measurement(self, integration_time=None, setting={}):
        '''Obtain a measurement with JETI Spectraval.
        
        If `integration_time` is not specified, will use  adaptive procedure
        (suitable for most situations).
    
        Parameters
        ----------
        integration_time : int
            The integration time to use for the measurement. Leave as None to
            to use JETI Spectraval adaptive procedure
        setting : dict, optional
             Current setting of the light source (if known), to be included in 
             the `info`. For example ``{'led' : 5, 'intensity' : 3000}``, or 
             ``{'intensities' : [0, 0, 0, 300, 4000, 200, 0, 0, 0, 0]}``. 
             The default is ``{}``.
    
        Returns
        -------
        spectrum : np.array
            JETI Spectraval spectral measurement
        info : dict
            Whatever other info we want from the spectrometer (e.g. PCB
            temperature)
    
        '''
        
        # Perform reference measurement
        self.ser.write(b'*MEAS:REFE 0 1 0\r')
        ack = self.ser.read(1)
        while ack != b'\x07':
            ack = self.ser.read(1)
            
        # Calculate spectral radiance
        self.ser.write(b'*CALC:SPRAD\r')
        data = self.ser.read(1606)
        data = np.array(data[2:], dtype=np.uint8)
        spectrum = np.array([x.view('<f')[0] for x in data])

        #more coe here for whatever else we want
        info = {**setting}
        
        return spectrum, info
    
    
    
# import csv
 
# with open("Projects/JETI/values.csv") as f:
#     r = csv.reader(f)
 
#     for line in r:
#         n = [int(float(i)) for i in line]
#         print(n)

# import numpy as np
# d = np.genfromtxt('Projects/JETI/values.csv', delimiter=',', dtype=np.uint8)
# spec = np.array([x.view('<f')[0] for x in d])


