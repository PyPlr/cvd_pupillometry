# -*- coding: utf-8 -*-
"""
Created on Wed Feb 17 11:49:40 2021

@author: engs2242
"""
from time import sleep
from pyplr import pupil

p = pupil.PupilCore()
p.command('R')
sleep(2)
label = ('LIGHT_ON')
annotation = pupil.new_annotation(label)
lst = p.lightstamper(annotation=annotation,
                     threshold=15,
                     timeout=10,
                     topic='frame.world')

print('bla')
sleep(1)
print('bla')
p.command('r')
lst.result()

lst = pupil.LightStamper(p, pupil.new_annotation('bla'), threshold=15, 
                 wait_time=None, subscription='frame.world')

label = 'LIGHT_ON'
annotation = pupil.new_annotation(label)
threshold = 15
timeout = 10.
p = pupil.PupilCore()
p.command('R')
sleep(2.)
lst = p.lightstamper(annotation, threshold, timeout)
sleep(timeout)
# light stimulus here
p.command('r')
lst.result()