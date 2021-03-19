#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from time import sleep

from psychopy import core, visual

from pyplr.pupil import PupilCore

def main(subject='test', display_size=(1024,768)):   

    # set up Pupil Core
    p = PupilCore()

    # setup windows and stims
    win = visual.Window(size=display_size, screen=1, color="black")
    white = visual.Rect(win, units='pix', size=display_size)
    white.color='white'
    black = visual.Rect(win, units='pix', size=display_size)
    black.color='black'

    # set up pupil trigger
    annotation = p.new_annotation('LIGHT_ON')

    p.command('R {}'.format(subject))
    sleep(2.)

    # start LightStamper
    lst_future = p.light_stamper(annotation, threshold=15, timeout=6.)

    # baseline
    sleep(2.)

    # present stimulus
    white.draw()
    win.flip()
    core.wait(1.0)
    black.draw()
    win.flip()

    print(lst_future.result())

    # Close the window
    win.close()

    # Close PsychoPy
    core.quit()

if __name__ == '__main__':    
    try:
        main()
    except KeyboardInterrupt:
        print('Killed by user')
        sys.exit(0)