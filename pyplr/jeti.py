#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
pyplr.jeti
==========

A (currently) bare bones serial interface for JETI Spectraval. 

@author: jtm
'''

import numpy as np
import matplotlib.pyplot as plt
import serial

class Spectraval:
    
    def __init__(self, 
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
        spectrum : `np.array`
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
            
        # Calculate spectral radiance and retrieve byte array
        # as 32-bit float. Note that the first two bytes are
        # not part of the spectrum.
        self.ser.write(b'*CALC:SPRAD\r')
        data = self.ser.read(1606)
        spec = np.frombuffer(data[2:], dtype=np.float32)
        
        #don't need this anymore as the above is quicker
        #data = np.array(data[2:], dtype=np.uint8)
        #spectrum = np.array([x.view('<f')[0] for x in data])

        #more code here for any device related info
        info = {**setting}
        
        return spec, info
    
#test

if __name__ == '__main__':
    device = Spectraval()
    specs = []
    for i in range(10):
        spectrum, _ = device.measurement()
        specs.append(spectrum)

    fig, ax = plt.subplots()
    for s in specs:
        ax.plot(s)          

