#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug  8 21:16:59 2020

@author: jtm
"""

from pyfirmata2 import Arduino
import time

board = Arduino(Arduino.AUTODETECT)
board.samplingOn(10)
#board.analog[0].register_callback(lambda x: print(x))
board.analog[0].enable_reporting()
while True:
    print(board.analog[0].read())

