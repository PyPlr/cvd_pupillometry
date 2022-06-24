#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
pyplr.stlabhelp
===============

Helper functions for STLab

"""
from typing import List, Any
from datetime import datetime
import json

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d


def make_spectrum_s(wavelengths, spectrum) -> List[int]:
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

#################################
# FUNCTIONS TO MAKE VIDEO FILES #
#################################


def _get_header(df, repeats=1):
    return {
        'version': 1,
        'model': 'VEGA10',
        'channels': 10,
        'spectracount': len(df),
        'transitionsCount': len(df),
        'fluxReference': 0,
        'repeats': repeats
    }


def _get_metadata(df, creator='jtm', **metadata):
    default = {
        'creation_time': str(datetime.now()),
        'creator': creator
    }
    return {**default, **metadata}


def _get_spectra(df):
    light_cols = df.columns[1:]
    return df[light_cols].values.tolist()


def _get_transitions(df):
    list_of_dicts = []
    for index, row in df.iterrows():
        list_of_dicts.append({
            'spectrum': index,
            'power': 100,
            'time': int(row['time']),
            'flags': 0
        })
    return list_of_dicts


def get_sinusoid_time_vector(duration):
    return np.arange(0, (duration * 1000), 10).astype('int')


def sinusoid_modulation(f, duration, Fs=100):
    x  = np.arange(duration * Fs)
    return np.sin(2 * np.pi * f * x / Fs)


def modulate_intensity_amplitude(sm, background, amplitude):
    return (background + (sm * amplitude)).astype('int')


def get_video_cols():
    cols = ['LED-' + str(val) for val in range(1, 11)]
    cols.insert(0, 'time')
    return cols


def _video_file_row(time=0, spec=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0]):
    fields = [time] + spec
    row = pd.DataFrame(fields).T
    cols = get_video_cols()
    row.columns = cols
    return row


def _video_file_end(end_time):
    df = pd.DataFrame()
    df = (df.append(_video_file_row(time=end_time))      # two extra dummy rows ensure the light
          .append(_video_file_row(time=end_time+100)))  # turns off when video file finishes
    return df


def make_video_file(df, fname='our_video_file', repeats=1, **metadata):
    """
    Takes a DataFrame with columns 'time', 'LED-1'...'LED-10'
    and save it as a .dsf ('dynamic sequence file') in the current
    working directory. The .dsf file can be loaded and played as a video stream
    with the STLAB.
    """
    d = {
        'header': _get_header(df, repeats),
        'metadata': _get_metadata(df, **metadata),
        'spectra': _get_spectra(df),
        'transitions': _get_transitions(df)
    }
    with open(fname + '.dsf', 'w') as outfile:
        json.dump(d, outfile)
    print(
        '"{}" saved in the current working directory.'.format(fname + '.dsf'))


def pulse_protocol(pulse_spec,
                   pulse_duration,
                   fname='our_video_file',
                   return_df=False,
                   metadata={}):
    """
    Generate a video file to deliver a pulse of light.

    Parameters
    ----------
    spec : list
        Sprectrum to use for the pulse of light.
    duration : int
        Duration of the pulse in ms.
    video_name : str
        Name for the video file.
    return_df : bool
        Whether to return the DataFrame used to create the video file.
    metadata : dict
        Additional info to include in the metadata of the video file (e.g.
        'color' : 'blue').

    Returns
    -------
    df : pd.DataFrame
        The DataFrame passed to make_video_file (if requested).

    """
    metadata['protocol'] = 'pulse'
    metadata['pulse_spec'] = str(pulse_spec)
    metadata['pulse_duration'] = str(pulse_duration)
    df = pd.DataFrame()
    df = (df.append(_video_file_row(0, pulse_spec))
          .append(_video_file_row(pulse_duration, pulse_spec))
          .append(_video_file_end(pulse_duration))
          .reset_index(drop=True))
    make_video_file(df, fname, **metadata)
    if return_df:
        return df


def background_pulse_protocol(background_spec,
                              pre_pulse_duration,
                              pulse_spec,
                              pulse_duration,
                              post_pulse_duration,
                              fname='our_video_file',
                              return_df=False,
                              metadata={}):
    """
    Generate a video file to deliver a pulse of light (or dark) against a
    background of light (or dark). Clunky but works well.

    Parameters
    ----------
    background_spec : list
        The background spectrum.
    pre_pulse_duration : int
        Duration of the background prior to pulse.
    pulse_spec : list
        The pulse spectrum..
    pulse_duration : int
        Duration of the pulse in ms.
    post_pulse_duration : int
        Duration of the background after the pulse..
    fname : str, optional
        Name for the video file. The default is 'our_video_file'.
    return_df : bool, optional
        Whether to return the DataFrame. The default is False.
    metadata : dict
        Additional info to include in the metadata field of the video file
        (e.g. {'color' : 'blue'}). This info can be extracted when loading the
        file during an experiment and included in triggers sent to Pupil
        Capture. The default is {}.

    Returns
    -------
    df : pd.DataFrame
        The DataFrame passed to make_video_file (if requested).

    """
    metadata['protocol'] = 'background_pulse'
    metadata['background_spec'] = background_spec
    metadata['pre_pulse_duration'] = int(pre_pulse_duration)
    metadata['pulse_spec'] = pulse_spec
    metadata['pulse_duration'] = int(pulse_duration)
    metadata['post_pulse_duration'] = int(post_pulse_duration)
    onset = pre_pulse_duration
    offset = onset+pulse_duration
    end = offset+post_pulse_duration
    df = pd.DataFrame()
    df = (df.append(_video_file_row(0, background_spec))
          .append(_video_file_row(pre_pulse_duration, background_spec))
          .append(_video_file_row(pre_pulse_duration, pulse_spec))
          .append(_video_file_row(
              pre_pulse_duration+pulse_duration, pulse_spec))
          .append(_video_file_row(
              pre_pulse_duration+pulse_duration, background_spec))
          .append(_video_file_row(end, background_spec))
          .append(_video_file_end(end))
          .reset_index(drop=True))
    make_video_file(df, fname, **metadata)
    if return_df:
        return df


def video_file_to_dict(video_file):
    """
    Unpack a video file into a dictionary with keys ['header', 'metadata',
    'spectra', 'transitions']

    Parameters
    ----------
    video_file : str
        The video file to unpack.

    Returns
    -------
    data : dict
        the video file as a dictionary.

    """
    with open(video_file) as vf:
        data = json.load(vf)
    return data


def get_led_colors(rgb=False):
    if rgb:
        colors = [
            [.220, .004, .773, 1.], [.095, .232, .808, 1.],
            [.098, .241, .822, 1.], [.114, .401, .755, 1.],
            [.194, .792, .639, 1.], [.215, .895, .489, 1.],
            [.599, .790, .125, 1.], [.980, .580, .005, 1.],
            [.975, .181, .174, 1.], [.692, .117, .092, 1.]
        ]
    else:
        colors = [
            'blueviolet', 'royalblue', 'darkblue', 'blue', 'cyan', 'green',
            'lime', 'orange', 'red', 'darkred'
        ]
    return colors


class VideoFile:
    def __init__(self, spectra, transitions):
        self.spectra = spectra
        self.transitions = transitions
        pass
    
    def from_csv(cls, fpath):
        pass
    
    def set_repeats(self):
        pass
    
    

