# -*- coding: utf-8 -*-
'''
Created on Wed Jun 17 15:21:46 2020

@author: JTM

A module to facilitate working with the PupilCore eye tracking headset. 

For more info go here:
https://docs.pupil-labs.com/developer/core/network-api/#pupil-remote

# TODO: use breakpoint() for debugging!

'''

import sys
from time import time
from threading import Thread

import numpy as np
import msgpack
import zmq

class PupilCore():
    '''
    A Class for Pupil Core and the remote helper.
    
    '''
    
    def __init__(self, address='127.0.0.1', request_port='50020', 
                 pyplr_defaults=True):
        '''
        Initialise the connection with Pupil Core. 

        Parameters
        ----------
        address : string, optional
            The IP address of the device. The default is '127.0.0.1'.
        request_port : string, optional
            Pupil Remote accepts requests via a REP socket, by default on 
            port 50020. Alternatively, you can set a custom port in Pupil Capture
            or via the --port application argument. The default is '50020'.
        pyplr_defaults : bool, optional
            Whether to configure Pupil Capture with the defaults used for pyplr
            LightStamper. This includes making sure the Annotation Capture plugin
            is active, that frames are published in BGR format, and that the
            world camera is using a frame rate of (320,240) at 120 hz with 
            exposure mode set to manual. Always manually verify that the settings
            are appropriate for the application you are running. 
            The default is True. 

        Returns
        -------
        None.

        '''
        self.address = address
        self.request_port = request_port
        
        # connect to pupil remote
        self.context = zmq.Context()
        self.remote = zmq.Socket(self.context, zmq.REQ)
        self.remote.connect(
            'tcp://{}:{}'.format(self.address, self.request_port))
            
        # request 'SUB_PORT' for reading data
        self.remote.send_string('SUB_PORT')
        self.sub_port = self.remote.recv_string()
        
        # request 'PUB_PORT' for writing data
        self.remote.send_string('PUB_PORT')
        self.pub_port = self.remote.recv_string()
        
        # open socket for publishing
        self.pub_socket = zmq.Socket(self.context, zmq.PUB)
        self.pub_socket.connect(
            'tcp://{}:{}'.format(self.address, self.pub_port))
        
        # some PyPlr defaults
        if pyplr_defaults:
            self.notify({
                'subject': 'start_plugin',
                'name': 'Annotation_Capture',
                'args': {}
                }) 
            self.notify({
                'subject': 'frame_publishing.set_format',
                'format': 'bgr'
                })
            self.notify({
                'subject': 'start_plugin',
                'name': 'UVC_Source',
                'args': {
                     'frame_size': (320,240),
                     'frame_rate': 120,
                     'name': 'Pupil Cam1 ID2',
                     'exposure_mode': 'manual'
                     }
                })

    def command(self, cmd):
        '''
        Send a command via Pupil Remote. 

        Parameters
        ----------
        cmd : string
            Must be one of the following:
                
            'R'          - start recording with auto generated session name
            'R rec_name' - start recording named "rec_name" 
            'r'          - stop recording
            'C'          - start currently selected calibration
            'c'          - stop currently selected calibration
            'T 1234.56'  - resets current Pupil time to given timestamp
            't'          - get current Pupil time; returns a float as string
            'v'          - get the Pupil Core software version string
            'PUB_PORT'   - return the current pub port of the IPC Backbone 
            'SUB_PORT'   - return the current sub port of the IPC Backbone

        Returns
        -------
        string
            the result of the command. If the command was not acceptable, this
            will be 'Unknown command.'

        '''
        # For every message that you send to Pupil Remote, you need to receive
        # the response. If you do not call recv(), Pupil Capture might become
        # unresponsive...
        self.remote.send_string(cmd)
        return self.remote.recv_string()
    
    def notify(self, notification):
        '''
        Send a notification to Pupil Remote. Every notification has a topic 
        and can contain potential payload data. The payload data has to be 
        serializable, so not every Python object will work. To find out which
        plugins send and receive notifications, open the codebase and search 
        for `.notify_all(` and `def on_notify(`. 
    
        Parameters
        ----------
        pupil_remote : zmq.sugar.socket.Socket
            the pupil remote helper.
        notification : dict
            the notification dict. Some examples:
                
            - {'subject': 'start_plugin', 'name': 'Annotation_Capture', 'args': {}}) 
            - {'subject': 'recording.should_start', 'session_name': 'my session'}
            - {'subject': 'recording.should_stop'}
            
        Returns
        -------
        string
            the response.

        '''
        topic = 'notify.' + notification['subject']
        payload = msgpack.dumps(notification, use_bin_type=True)
        self.remote.send_string(topic, flags=zmq.SNDMORE)
        self.remote.send(payload)
        return self.remote.recv_string()
    
    def send_trigger(self, trigger):
        '''
        Send an annotation (a.k.a 'trigger') to Pupil Capture. Use to mark the 
        timing of events.
        
        Parameters
        ----------
        trigger : dict
            customiseable - see the new_trigger(...) function.
    
        Returns
        -------
        None.
    
        '''
        payload = msgpack.dumps(trigger, use_bin_type=True)
        self.pub_socket.send_string(trigger['topic'], flags=zmq.SNDMORE)
        self.pub_socket.send(payload)
    

class LightStamper(Thread):
    '''
    A thread-bound class which uses the Pupil Core World Camera to detect the 
    onset of a light and send an annotation (a.k.a 'trigger') to Pupil Capture 
    with the associated Pupil timestamp. Useful for integrating with virtually
    any light source. Supports extraction of PLRs and calculation of time-critical 
    measures such as latency and time-to-peak consctriction. Inherits from 
    threading.Thread and overrides the .run() method. Instantiate a few seconds 
    before administering a light stimulus. Works very well with the following 
    settings in Pupil Capture:
        
    1. Resolution (320, 240) for eye and world
    2. Frame rate 120 for eye and world
    3. Auto Exposure mode - Manual Exposure - eye and world
    4. Absolute exposure time 60 for world, 63 for eye
    5. Frame publisher format - BGR

    Example
    -------
    label = 'LIGHT_ON'
    trigger = new_trigger(label)
    threshold = 15
    wait_time = 5.
    lst = LightStamper(pupil, trigger, threshold, wait_time)
    lst.start()
        
    '''
    def __init__(self, pupil, trigger, threshold=15, 
                 wait_time=None, subscription='frame.world'):
        '''
        Prepare to stamp a light. Follow up with LightStamper.start() to begin.
        
        Parameters
        ----------
        pupil : pupil.PupilCore
            PupilCore class instance
        trigger : dict
            a dictionary with at least the following:
                
            {'topic': 'annotation',
             'label': 'our_label',
             'timestamp': None}
            
            timestamp will be overwritten with the new pupil timestamp for the 
            detected light. See new_trigger(...) for more info.
        threshold : int
            detection threshold for luminance increase. The right value depends on
            the nature of the light stimulus and the ambient lighting conditions. 
            Requires some guesswork right now, but it would be good to have a 
            function that works it out for us. 
        wait_time : float, optional
            time to wait in seconds before giving up (will run indefinitely if
            no value is passed, in which case will require LightStamper.join()). 
            Use when controlling a light source programmatically. For STLAB, use 
            6.0 s, because on rare occasions it can take about 5 seconds 
            to process a request. The default in None. 
        subscription : string
            The camera frames to subscribe to. In most cases this will be 
            'frame.world', but the method will also work for 'frame.eye.0' and
            'frame.eye.1' if the light source contains enough near-infrared. 
            The default is 'frame.world'.
        detected : bool
            Whether a light gets detected.
        timestamp : None, float
            The pupil timestamp associated with the frame where the light was
            detected.
            
        Returns
        -------
        None.

        '''
        super(LightStamper, self).__init__()
        self.pupil = pupil
        self.trigger = trigger
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
        '''
        Override the threading.Thread.run() method with light detection code. 
        This code works by keeping track of the two most recent frames from the 
        World Camera. When the difference between the two is greater than
        the given threshold, a trigger is sent via pupil remote with the 
        timestamp corresponding to the most recent frame. 

        Returns
        -------
        None.

        '''
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
                    self.trigger['timestamp'] = recent_world_ts # change trigger timestamp
                    self.pupil.send_trigger(self.trigger)
                    self.timestamp = recent_world_ts
                    self.successful = True
            recent_world_minus_one = recent_world
            if self.wait_time > 0:
                t2 = time()
        if self.successful == False:
            print('LightStamper failed to detect a light...')

class PupilGrabber(Thread):
    '''
    A thread-bound class for grabbing data from Pupil Core. 
    
    Example
    -------
    pupil = PupilCore()
    pg = PupilGrabber(pupil, topic='pupil.0.3d', secs=10)
    pg.start()
    
    '''
    def __init__(self, pupil, topic, secs=None):
        '''
        Prepare to start grabbing some data from pupil. Follow up with 
        PupilGrabber.start() to begin.

        Parameters
        ----------
        pupil : pupil.PupilCore
            PupilCore class instance
        topic : string
            Subscription topic. Can be:
                
                'pupil.0.2d'  - 2d pupil datum (left)
                'pupil.1.2d'  - 2d pupil datum (right)  
                'pupil.0.3d'  - 3d pupil datum (left)
                'pupil.1.3d'  - 3d pupil datum (right)  
                'gaze.3d.1.'  - monocular gaze datum
                'gaze.3d.01.' - binocular gaze datum
                'logging'     - logging data
                
            Other topics are available from plugins (e.g. fixations, surfaces)
            and custom topics can be defined. 
        secs : float, optional
            Ammount of time to spend grabbing data. Will run indefinitely if 
            no value is passed, in which case requires PupilGrabber.join().

        Returns
        -------
        None.

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
        '''
        Override the threading.Thread.run() method with code for grabbing data.

        Returns
        -------
        None.

        '''
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
        '''
        Get grabbed data.

        Parameters
        ----------
        what : string
            The key of the data to be accessed. E.g. 'diameter_3d', 'timestamp',
            'gaze_point_3d'.

        Returns
        -------
        np.array()
            The requested data.

        '''
        return [entry[what.encode()] for entry in self.data]
            
def notify(pupil_remote, notification):
    '''
    Send a notification to Pupil Remote.

    Parameters
    ----------
    pupil_remote : zmq.sugar.socket.Socket
        the pupil remote helper.
    notification : dict
        the notification dict. 
        e.g. {'subject':'start_plugin', 'name':'Annotation_Capture'}
    Returns
    -------
    string
        the response.

    '''
    topic = 'notify.' + notification['subject']
    payload = msgpack.dumps(notification, use_bin_type=True)
    pupil_remote.send_string(topic, flags=zmq.SNDMORE)
    pupil_remote.send(payload)
    return pupil_remote.recv_string()

def send_trigger(pub_socket, trigger):
    '''
    Send an annotation (a.k.a 'trigger') to Pupil Capture. Use to mark the 
    timing of events.
    
    Parameters
    ----------
    pub_socket : zmq.sugar.socket.Socket
        a socket to publish the trigger.
    trigger : dict
        customiseable - see the new_trigger(...) function.

    Returns
    -------
    None.

    '''
    payload = msgpack.dumps(trigger, use_bin_type=True)
    pub_socket.send_string(trigger['topic'], flags=zmq.SNDMORE)
    pub_socket.send(payload)
    
def new_trigger(label, custom_fields={}):
    '''
    Create a new trigger / annotation / message / event marker / whatever 
    you want to call it. Send it to Pupil Capture with the send_trigger(...) 
    function.

    Parameters
    ----------
    label : string
        A label for the event.
    custom_fields : dict, optional
        Any additional information to add (e.g. {'duration':2, 'color':'blue'}). 
        The default is {}.

    Returns
    -------
    trigger : dict
        The trigger dictionary, ready to be sent.

    '''
    trigger = {
        'topic': 'annotation',
        'label': label,
        'timestamp': time()
        }
    for k, v in custom_fields.items():
        trigger[k] = v
    return trigger

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
    payload = msgpack.unpackb(subscriber.recv(), encoding='utf-8')
    extra_frames = []
    while subscriber.get(zmq.RCVMORE):
        extra_frames.append(subscriber.recv())
    if extra_frames:
        payload['__raw_data__'] = extra_frames
    return topic, payload

       
# def find_threshold(subscriber):
#     world_data = []
#     print('Shine a light...')
#     while True:
#         topic, msg = recv_from_subscriber(subscriber)
#         recent_world = np.frombuffer(
#             msg['__raw_data__'][0], dtype=np.uint8).reshape(
#                 msg['height'], msg['width'], 3)
#         world_data.append(recent_world.mean())

