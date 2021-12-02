#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pyplr.graphing
==============

Functions to help with plotting.

@author: jtm
"""

import matplotlib.pyplot as plt


def pupil_preprocessing_figure(nrows, subject, **kwargs):
    """Set up a figure to show the stages of pupil data processing.

    Parameters
    ----------
    nrows : int
        Number of rows in the figure.
    subject : str
        The subject identifier (used for the title of the plot).
    **kwargs : dict
        Subplot kwargs.

    Returns
    -------
    f : plt.Figure
        The figure handle.
    axs : list
        List of axes.

    """

    fig, axs = plt.subplots(
        nrows=nrows, ncols=1, sharex=True, figsize=(14, 14), **kwargs)

    for ax in axs:
        ax.set_ylabel('Pupil diameter')
        ax.set_xlabel('Pupil timestamp')

    axs[0].legend(loc='upper right', labels=['pixels', 'mm'])
    fig.suptitle('Preprocessing for subject: {}' .format(subject))

    return fig, axs
