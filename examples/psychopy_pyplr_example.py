#!/usr/bin/env python
# -*- coding: utf-8 -*-

# would be nice to include a basic PsychoPy script that works with a standard monitor.
# requires pyglet=1.4.10 to avoid threading error

from __future__ import print_function
from time import sleep
from psychopy import core, event, visual
from pyplr.pupil import PupilCore

def change_color(win, color, log=False):
    win.color = color
    if log:
        print('Changed color to %s' % win.color)

win = visual.Window(color=[0.,0.,0.])
# text = visual.TextStim(win,
#                       text='Press C to flash light')

# Global event key to change window background color.
# event.globalKeys.add(key='c',
#                     func=change_color,
#                     func_args=[win],
#                     func_kwargs=dict(log=True),
#                     name='change window color')

# Global event key (with modifier) to quit the experiment ("shutdown key").
# event.globalKeys.add(key='q', modifiers=['ctrl'], func=core.quit)

# Connect to Pupil Core
p = PupilCore()

# Start recording
p.command('R')
sleep(5)

annotation = p.new_annotation(label='LIGHT_ON')
lst = p.light_stamper(annotation=annotation, 
                      threshold=15,
                      timeout=10, 
                      topic='frame.world')
sleep(2)
change_color(win, color=[1.,1.,1.])
win.flip()
sleep(1)
change_color(win, color=[0.,0.,0.])
win.flip()
sleep(2)

# End recording
p.command('r')

#lst.result()