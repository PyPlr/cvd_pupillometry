# -*- coding: utf-8 -*-
"""
Created on Fri Feb 19 11:35:49 2021

@author: engs2242
"""
from time import time
from threading import Thread

import numpy as np
import msgpack
import zmq

class LightStamper(Thread):
    '''Detect and time-stamp light onsets using the Pupil Core World Camera. 
    
    Currently implemented as a sublclass of threading.Thread for easy 
    access to data after the task is complete. Supports extraction of PLRs and 
    calculation of time-critical measures such as latency and time-to-peak 
    consctriction. Instantiate a few seconds before administering a light 
    stimulus. 

    Example
    -------
    >>> label = 'LIGHT_ON'
    >>> annotation = new_annotation(label)
    >>> threshold = 15
    >>> wait_time = 5.
    >>> lst = LightStamper(pupil, annotation, threshold, wait_time)
    >>> lst.start()
    
    Note
    ----
    Requires a suitable geometry and for the World Camera to be pointed at the 
    light source. Also requires the following settings in Pupil Capture:
        
    * Auto Exposure mode - Manual Exposure (eye and world)
    * Frame publisher format - BGR
    
    '''
    def __init__(self, pupil, annotation, threshold=15, 
                 wait_time=None, subscription='frame.world'):
        '''Set up subscription and prepare to stamp a light. 
        
        Parameters
        ----------
        pupil : pupil.PupilCore
            `PupilCore` class instance.
        annotation : dict
            A dictionary with at least the following::
                
                {
                 'topic': 'annotation',
                 'label': '<your label>',
                 'timestamp': None
                 }
                
            timestamp will be overwritten with the new pupil timestamp for the 
            detected light. See `new_annotation(...)` for more info.
        threshold : int
            Detection threshold for luminance increase. The right value depends on
            the nature of the light stimulus and the ambient lighting conditions. 
            Requires some guesswork right now, but it would be good to have a 
            function that works it out for us. 
        wait_time : float, optional
            Time to wait in seconds before giving up (will run indefinitely if
            no value is passed, in which case will require `LightStamper.join()`). 
            Use when controlling a light source programmatically. For STLAB, use 
            6.0 s, because on rare occasions it can take about 5 seconds 
            to process a request. The default in None. 
        subscription : string
            The camera frames to subscribe to. In most cases this will be 
            `'frame.world'`, but the method will also work for `'frame.eye.0'`
            and `'frame.eye.1'` if the light source contains enough near-infrared. 
            The default is `'frame.world'`.
        detected : bool
            Whether a light gets detected.
        timestamp : None, float
            The pupil timestamp associated with the frame where the light was
            detected.
            
        '''
        super(LightStamper, self).__init__()
        self.pupil = pupil
        self.annotation = annotation
        self.threshold = threshold
        self.wait_time = wait_time
        self.subscription = subscription
        self.successful = False
        self.timestamp = None

        # a unique, encapsulated subscription to avoid race conditions
        self.subscriber = self.pupil.context.socket(zmq.SUB)
        self.subscriber.connect(
            'tcp://{}:{}'.format(pupil.address, pupil.sub_port))
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, self.subscription)
        
    def run(self):
        '''This method has been overridden with the `stamp_light()` method.
        
        Note
        ----
        This is an isiosyncratic approach which we adopt because it simplifies
        access to data from the thread.

        '''
        self.stamp_light()
        
    def stamp_light(self):
        '''The light detection algorithm.
        
        Keeps track of the two most recent frames from the World Camera. When
        the difference between the two is greater than `self.threshold`, an 
        annotation is sent via pupil remote with the timestamp corresponding to 
        the most recent frame. 
        
        '''
        # TODO: review this algo
        recent_world = None
        recent_world_minus_one = None
        recent_world_ts = None
        if self.wait_time is None:
            self.wait_time, t1, t2 = 0, -1, -2 # dummy values
        else:
            t1 = time()
            t2 = time()
        print('Waiting for a light to stamp...')
        while not self.successful and (t2-t1) < self.wait_time:
            topic, msg = recv_from_subscriber(self.subscriber)
            if topic == self.subscription:
                recent_world = np.frombuffer(
                    msg['__raw_data__'][0], dtype=np.uint8).reshape(
                        msg['height'], msg['width'], 3)
                recent_world_ts = msg['timestamp']
            if recent_world is not None and recent_world_minus_one is not None:
                diff = recent_world.mean() - recent_world_minus_one.mean()
                if diff > self.threshold:
                    print('Light stamped on {} at {}'.format(
                        self.subscription, recent_world_ts))
                    self.annotation['timestamp'] = recent_world_ts # change annotation timestamp
                    self.pupil.send_annotation(self.annotation)
                    self.timestamp = recent_world_ts
                    self.successful = True
            recent_world_minus_one = recent_world
            if self.wait_time > 0:
                t2 = time()
        if self.successful == False:
            print('LightStamper failed to detect a light...')

class PupilGrabber(Thread):
    '''Start grabbing data from Pupil Core.
        
    Example
    -------
    >>> pupil = PupilCore()
    >>> pgr = PupilGrabber(pupil, topic='pupil.0.3d', secs=10)
    >>> pgr.start()
    >>> sleep(10.)
    >>> data = pgr.get('diameter_3d')
    
    '''
    def __init__(self, pupil, topic, secs=None):
        '''
        Prepare subscriptions for data grabbing. Follow up with 
        `PupilGrabber.start()`.

        Parameters
        ----------
        pupil : pupil.PupilCore
            PupilCore class instance.
        topic : string
            Subscription topic. Can be:
                
                * 'pupil.0.2d'  - 2d pupil datum (left)
                * 'pupil.1.2d'  - 2d pupil datum (right)  
                * 'pupil.0.3d'  - 3d pupil datum (left)
                * 'pupil.1.3d'  - 3d pupil datum (right)  
                * 'gaze.3d.1.'  - monocular gaze datum
                * 'gaze.3d.01.' - binocular gaze datum
                * 'logging'     - logging data
                
            Other topics are available from plugins (e.g. fixations, surfaces)
            and custom topics can be defined. 
        secs : float, optional
            Ammount of time to spend grabbing data. Will run indefinitely if 
            no value is passed, in which case requires PupilGrabber.join().

        '''
        super(PupilGrabber, self).__init__()
        self.pupil = pupil
        self.topic = topic
        self.secs = secs
        self.data = []
        
        # a unique, encapsulated subscription
        self.subscriber = self.pupil.context.socket(zmq.SUB)
        self.subscriber.connect(
            'tcp://{}:{}'.format(self.pupil.address, self.pupil.sub_port))
        self.subscriber.subscribe(self.topic)
        # TODO: add check on topic subscription

    def run(self):
        '''This method has been overridden with the `grab()` method.
        
        Note
        ----
        This is an isiosyncratic approach which we adopt because it simplifies
        access to data from the thread.

        '''
        self.grab()
        
    def grab(self):
        '''The pupil grabbing algorithm.
        
        Grabs all messages which match `self.topic` and dumps them in `self.data`
        
        '''
        # TODO: review algo
        print('PupilGrabber now grabbing {} seconds of {}'.format(
            '?' if not self.secs else self.secs, self.topic))
        if not self.secs:
            self.secs, t1, t2 = 0, -1, -2 # dummy values
        else:
            t1, t2 = time(), time()
        while t2 - t1 < self.secs:
            topic, payload = self.subscriber.recv_multipart()
            message = msgpack.loads(payload)
            self.data.append(message)
            t2 = time()
        print('PupilGrabber done grabbing {} seconds of {}'.format(
            self.secs, self.topic))
        
    def get(self, what):
        '''Get grabbed data.

        Parameters
        ----------
        what : string
            The key of the data to be accessed. E.g., 'diameter_3d', 'timestamp',
            'gaze_point_3d'.

        Returns
        -------
        np.array()
            The requested data.

        '''
        # TODO: allow for accessing multiple data types and return a dict
        return [entry[what.encode()] for entry in self.data]
            
def recv_from_subscriber(subscriber):
    '''
    Receive a message with topic and payload.
    
    Parameters
    ----------
    subscriber : zmq.sugar.socket.Socket
        a subscriber to any valid topic.

    Returns
    -------
    topic : str
        A utf-8 encoded string, returned as a unicode object.
    payload : dict
        A msgpack serialized dictionary, returned as a python dictionary.
        Any addional message frames will be added as a list in the payload 
        dictionary with key: '__raw_data__'. To use frame data, say: 
        np.frombuffer(msg['__raw_data__'][0], dtype=np.uint8).reshape(
        msg['height'], msg['width'], 3)
        
    '''
    topic = subscriber.recv_string()
    payload = msgpack.unpackb(subscriber.recv())
    extra_frames = []
    while subscriber.get(zmq.RCVMORE):
        extra_frames.append(subscriber.recv())
    if extra_frames:
        payload['__raw_data__'] = extra_frames
    return topic, payload