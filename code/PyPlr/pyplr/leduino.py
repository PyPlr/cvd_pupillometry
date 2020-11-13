# -*- coding: utf-8 -*-
'''
Created on Sat Aug  8 21:04:55 2020
@author: jtm
A module for Arduino-based tools.
'''

from threading import Thread
from time import time

class LEDuinoDetect(Thread):
    '''    
    A thread-bound class which uses and Arduino-phototransistor circuit to 
    detect the onset of a light and send an annotation (a.k.a 'trigger') to  
    Pupil Capture with the associated Pupil timestamp. Works just like
    pupil.LightStamper, but lags by about 30-60 ms.    
    '''        
    def __init__(self, pupil, board, trigger, threshold, wait_time=None):
        super(LEDuinoDetect, self).__init__()
        self.pupil = pupil
        self.board = board
        self.trigger = trigger
        self.threshold = threshold 
        self.wait_time = wait_time     
        self.successful = False      
        self.timestamp = None       
        
        # override threading.Thread.run() method with light detection code  
        def run(self):    
            recent_val = None    
            recent_val_minus_one = None    
            if self.wait_time is None:    
                self.wait_time, t1, t2 = 0, -1, -2 # dummy values   
            else:       
                t1 = time()      
                t2 = time()   
            print('LEDuino waiting for a light to stamp...')    
            while not self.successful and (t2 - t1) < self.wait_time: 
                recent_val = self.board.analog[0].read()  
                if recent_val is not None and recent_val_minus_one is not None:     
                    diff = recent_val - recent_val_minus_one     
                    print(recent_val)         
                    if diff > self.threshold:       
                        self.timestamp = time()       
                        print('Light stamped at {}'.format(self.timestamp))          
                        self.trigger['timestamp'] = self.timestamp # change trigger timestamp      
                        self.pupil.send_trigger(self.trigger)     
                        self.successful = True         
                        recent_val_minus_one = recent_val   
                if self.wait_time > 0:          
                    t2 = time()      
                if self.successful == False:     
                    print('LEDuinoDetect failed to detect a light...')
