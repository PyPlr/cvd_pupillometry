#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 10 10:17:19 2021

@author: jtm
"""

from pyplr.pupil import PupilCore

p = PupilCore()

props = p.get_pupil_detector_properties('Pye3DPlugin', 1)
