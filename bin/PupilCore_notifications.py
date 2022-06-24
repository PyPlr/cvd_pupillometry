#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  3 17:49:05 2020

@author: jtm

A handy list of notification dicts
"""

{
    "subject": "pupil_detector.set_property.3d",
    "name": "model_is_frozen",
    "value": True,  # set to False to unfreeze
    "target": "eye0",  # remove this line if you want to freeze the model both eyes
}

{
    'subject':'start_plugin',
    'name':'Annotation_Capture',
    'args':{}
}
 
{
    'subject':'frame_publishing.set_format',
    'format':'bgr'
}

{
    'subject':'start_plugin',
    'name':'UVC_Source',
    'args':{
        'frame_size':(320,240),
        'frame_rate':120,
        'name':'Pupil Cam1 ID2',
        'exposure_mode':'manual'}
}

    