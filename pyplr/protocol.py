# -*- coding: utf-8 -*-
"""
pyplr.plr
=========

Tools for designing pupillometry protocols.

@author: jtm

"""

import os
import os.path as op
from time import sleep


def input_subject_id() -> str:
    """Request an identifier for the subject.

    Returns
    -------
    str
        Subject identifier.

    """
    return input('Please enter subject ID: ')


def subject_dir(subject_id: str) -> str:
    """Make a new directory (if it doesn't already exist) with name subject_id.

    Parameters
    ----------
    subject_id : str
        An identifier for the subject.

    Returns
    -------
    subj_dir : str
        Path to the subject directory.

    """
    subj_dir = op.join(os.getcwd(), subject_id)
    if not op.isdir(subj_dir):
        os.mkdir(subj_dir)
    return subj_dir


def new_record_id(subj_dir: str) -> str:
    """Make a new zero-padded identifier for the recording.

    Parameters
    ----------
    subj_dir : str
        Path to the subject directory.

    Returns
    -------
    str
        A unique (within `subject_dir`) zero-padded identifier of length three.

    """
    recording_id = 0
    for base, _, _ in os.walk(subj_dir):
        if 'rec' + str(recording_id).zfill(3) == op.basename(base):
            recording_id += 1
    return 'rec' + str(recording_id).zfill(3)


def record_dir(subj_dir: str) -> str:
    """Make a new recording directory.

    Parameters
    ----------
    subj_dir : str
        Path to where the new directory should be made.

    Returns
    -------
    rec_dir : str
        Path to the recording directory.

    """
    record_id = new_record_id(subj_dir)
    rec_dir = op.join(subj_dir, record_id)
    if not op.isdir(subj_dir):
        os.mkdir(subj_dir)
    if not op.isdir(rec_dir):
        os.mkdir(rec_dir)
    return rec_dir


def timer(increment: int = 1,
          seconds: int = 0,
          message: str = 'Waiting...') -> None:
    """Count down to next event.

    Parameters
    ----------
    increment : int, optional
        Number of seconds between each feedback statement. The default is 1.
    seconds : int, optional
        Number of seconds to wait. The default is 0.
    message : str, optional
        Feedback message. The default is 'Waiting...'.

    Returns
    -------
    None.

    """
    print(message)
    while seconds > 0:
        print(f'\t{seconds} seconds left...')
        sleep(increment)
        seconds -= increment
