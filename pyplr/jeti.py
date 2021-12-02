#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pyplr.jeti
==========

A (currently) bare bones serial interface for JETI Spectraval.

@author: jtm
"""

from typing import Tuple

import numpy as np
import matplotlib.pyplot as plt
import serial


class Spectraval:
    """Interface to JETI Spectraval.

    """

    def __init__(self,
                 port: str = '/dev/cu.usbserial-DJ5F3W9U',
                 baudrate: int = 921600,
                 bytesize: int = 8,
                 stopbits: int = 1,
                 parity: str = 'N',
                 timeout: int = 240):

        # open serial connection
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=bytesize,
            stopbits=stopbits,
            parity=parity,
            timeout=timeout)

    def measurement(self, setting: dict = None) -> Tuple[np.array, dict]:
        """Obtain a measurement with JETI Spectraval.

        Parameters
        ----------
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

        """

        # Perform reference measurement and wait for acknowledgement.
        self.ser.write(b'*MEAS:REFER 0 1 0\r')
        ack = self.ser.read(1)
        while ack != b'\x07':
            ack = self.ser.read(1)

        # Calculate spectral radiance and retrieve byte array as 32-bit float.
        # Note that the first two bytes are not part of the spectrum.
        self.ser.write(b'*CALC:SPRAD\r')
        data = self.ser.read(1606)
        spec = np.frombuffer(data[2:], dtype=np.float32)

        # Add the luminaire setting, if given, to the info.
        info = {}
        if setting is not None:
            if not isinstance(setting, dict):
                raise TypeError('Setting must be of type dict')
            info = {**setting}

        return (spec, info)

    def wavelengths(self) -> np.array:
        return np.arange(380, 781, 1)


# Test
if __name__ == '__main__':
    device = Spectraval()
    specs = []
    for i in range(10):
        spectrum, _ = device.measurement()
        specs.append(spectrum)

    fig, ax = plt.subplots()
    for s in specs:
        ax.plot(s)
