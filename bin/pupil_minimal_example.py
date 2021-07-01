#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 13 20:45:12 2021

@author: jtm
"""

from time import sleep

from pyplr.pupil import PupilCore

# Set up pupil core
p = PupilCore()

# Start a recording
p.command('R my_recording')

# Annotation to be sent when the light comes on
annotation = p.new_annotation('LIGHT_ON')

# Start light_stamper and pupil_grabber
lst_future = p.light_stamper(annotation=annotation, timeout=12)
pgr_future = p.pupil_grabber(topic='pupil.1.3d', seconds=12)

# Wait a few seconds...
sleep(12)

# Administer light stimulus here

# Stop recording
p.command('r')

