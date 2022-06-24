# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 10:40:13 2022

@author: jtm

Demonstrates how to retrieve pupil detector properties from Pupil Capture.

"""

from time import sleep
from pyplr.pupil import PupilCore
from pprint import pprint

p = PupilCore()

s = p.subscribe_to_topic(topic='notify.pupil_detector.properties')

sleep(1.)

p.notify({
    'topic': 'notify.pupil_detector.broadcast_properties',
    'subject': 'pupil_detector.broadcast_properties',
    'eye_id': 0
})

properties = p.recv_from_subscriber(s)
pprint(properties)
