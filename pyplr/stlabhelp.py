#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
pyplr.stlabhelp
===============

Helper functions for STLab

"""

from typing import List, Array
from scipy.interpolate import interp1d


def make_spectrum_s(wavelengths: Array, spectrum: Array) -> List[int]:
    """Format a spectrum for STLab's SET_SPECTRUM_S command.
    

    Parameters
    ----------
    wavelengths : array-like
        Spectrometer wavelengths.
    spectrum : array-like
        Spectral measurement.

    Returns
    -------
    list
        List of 81 integers between 0 and 65535.

    """
    f = interp1d(wavelengths, spectrum)
    new_wls = range(380, 781, 5)
    spectrum_s = f(new_wls)
    spectrum_s = (spectrum_s / max(spectrum_s)) * 65535
    return [int(val) for val in spectrum_s]