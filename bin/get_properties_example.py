# -*- coding: utf-8 -*-
"""
Created on Fri Feb 19 10:40:13 2021

@author: engs2242
"""

from time import sleep
from pyplr.pupil import PupilCore

p = PupilCore()

s = p.subscribe_to_topic(topic='notify.pupil_detector.properties')

sleep(1.)

p.notify({
    'topic': 'notify.pupil_detector.broadcast_properties',
    'subject': 'pupil_detector.broadcast_properties',
    'eye_id': 0
    })

properties = p.recv_from_subscriber(s)
print(properties)
