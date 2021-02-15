#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
pyplr.pupil
===========

A module for interfacing with a Pupil Core eye tracker.

'''

from time import time
from threading import Thread
import concurrent.futures

import numpy as np
import msgpack
import zmq

class PupilCore:
    '''
    A class for Pupil Core and the Remote Helper.
    
    Example
    -------
    >>> # A two second recording
    >>> p = PupilCore()
    >>> p.command('R my_recording')
    >>> sleep(2.)
    >>> p.command('r')
    
    '''
    
    def __init__(self, address='127.0.0.1', request_port='50020', 
                 pyplr_defaults=True):
        '''
        
        Parameters
        ----------
        address : string, optional
            The IP address of the device. The default is `127.0.0.1`.
        request_port : string, optional
            Pupil Remote accepts requests via a REP socket, by default on 
            port 50020. Alternatively, you can set a custom port in Pupil Capture
            or via the `--port` application argument. The default is `50020`.
        pyplr_defaults : bool, optional
            Whether to configure Pupil Capture with the defaults used for pyplr.
            LightStamper. This includes making sure the Annotation Capture plugin
            is active, that frames are published in BGR format, and that the
            world camera is using a frame rate of (320,240) at 120 hz with 
            exposure mode set to manual. Always manually verify that the settings
            are appropriate for the application you are running. 
            The default is True. 
            
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
        
        # some useful defaults
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
        
        Note
        ----
        Click `here <https://docs.pupil-labs.com/developer/core/network-api/
        #pupil-remote>`_ for more information on Pupil Remote.
   
        Parameters
        ----------
        cmd : string
            Must be one of the following:
                
                * 'R'          - start recording with auto generated session name
                * 'R rec_name' - start recording named `rec_name` 
                * 'r'          - stop recording
                * 'C'          - start currently selected calibration
                * 'c'          - stop currently selected calibration
                * 'T 1234.56'  - resets current Pupil time to given timestamp
                * 't'          - get current Pupil time; returns a float as string
                * 'v'          - get the Pupil Core software version string
                * 'PUB_PORT'   - return the current pub port of the IPC Backbone 
                * 'SUB_PORT'   - return the current sub port of the IPC Backbone

        Returns
        -------
        string
            The result of the command. If the command was not acceptable, this
            will be 'Unknown command.'

        '''
        # For every message that you send to Pupil Remote, you need to receive
        # the response. If you do not call recv(), Pupil Capture might become
        # unresponsive...
        self.remote.send_string(cmd)
        return self.remote.recv_string()
    
    def notify(self, notification):
        '''
        Send a notification to Pupil Remote. 
        
        Every notification has a topic and 
        can contain potential payload data. The payload data has to be serializable,
        so not every Python object will work. To find out which plugins send and
        receive notifications, open the codebase and search for ``.notify_all(``
        and ``def on_notify(``. 
        
        Note
        ----
        Click `here <https://docs.pupil-labs.com/developer/core/network-api/
        #notification-message>`_ for more info on notifications.
        
        Parameters
        ----------
        notification : dict
            The notification dict. For example::
                
                {
                 'subject': 'start_plugin',
                 'name': 'Annotation_Capture',
                 'args': {}})
                }
            
        Returns
        -------
        string
            The response.

        '''
        topic = 'notify.' + notification['subject']
        self.remote.send_string(topic, flags=zmq.SNDMORE)
        payload = msgpack.dumps(notification, use_bin_type=True)
        self.remote.send(payload)
        return self.remote.recv_string()
    
    def send_annotation(self, annotation):
        '''Send an annotation (a.k.a trigger, event marker) to Pupil Capture. 
        
        Use to mark the timing of events.
        
        Parameters
        ----------
        annotation : dict
            Customiseable - see the `new_annotation(...)` function.
        
        Returns
        -------
        None.
     
        '''
        payload = msgpack.dumps(annotation, use_bin_type=True)
        self.pub_socket.send_string(annotation['topic'], flags=zmq.SNDMORE)
        self.pub_socket.send(payload)
    
    def lightstamper(self, annotation, threshold=15, timeout=None, 
                         subscription='frame.world'):
        '''Mark the onset of a luminance increase with the World Camera. 
        
        Executes the ``detect_light_onset(...)`` method in a thread using
        ``concurrent.futures.ThreadPoolExecutor()``, which allows future access 
        to the return value.
        
        Parameters
        ----------
        annotation : dict
            A dictionary with at least the following::
                
                {
                 'topic': 'annotation',
                 'label': '<your label>',
                 'timestamp': None
                 }
                
            timestamp will be overwritten with the new pupil timestamp for the 
            detected light. See ``new_annotation(...)`` for more info.
        threshold : int
            Detection threshold for luminance increase. The right value depends on
            the nature of the light stimulus and the ambient lighting conditions. 
            Requires some guesswork right now, but it would be good to have a 
            function that works it out for us. 
        timeout : float, optional
            Time to wait in seconds before giving up (will run indefinitely if
            no value is passed, in which case will require ``lightstamper.join()``). 
            Use when controlling a light source programmatically. For STLAB, use 
            6.0 s, because on rare occasions it can take about 5 seconds 
            to process a request. The default in None. 
        subscription : string
            The camera frames to subscribe to. In most cases this will be 
            `'frame.world'`, but the method will also work for `'frame.eye.0'`
            and `'frame.eye.1'` if the light source contains enough near-infrared. 
            The default is `'frame.world'`.
            
        Example
        -------
        >>> label = 'LIGHT_ON'
        >>> annotation = new_annotation(label)
        >>> threshold = 15
        >>> timeout = 10.
        >>> p = PupilCore()
        >>> p.command('R')
        >>> sleep(2.)
        >>> lst = pupil.lightstamper(annotation, threshold, timeout)
        >>> sleep(timeout)
        >>> # light stimulus here
        >>> p.command('r')
        
        Note
        ----
        Requires a suitable geometry and for the World Camera to be pointed at 
        the light source. Also requires the following settings in Pupil Capture:
            
        * Auto Exposure mode - Manual Exposure (eye and world)
        * Frame publisher format - BGR
        
        Returns
        -------
        concurrent.futures._base_Future
            An object that can be used to access the result of thread

        '''
        args = (annotation, threshold, timeout, subscription)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return executor.submit(self.detect_light_onset, *args)
    
    def detect_light_onset(self, annotation, threshold, timeout, subscription):
        '''Algorithm to detect onset of light stimulus with the World Camera.
        
        '''
        subscriber = self.subscribe_to_camera_frames(subscription)
        print('Waiting for a light to stamp...')
        start_time = time()
        previous_frame, _ = self.get_next_frame_from_worldcam(
            subscriber, subscription)
        while True:
            current_frame, timestamp = self.get_next_frame_from_worldcam(
                subscriber, subscription)
            if self._luminance_jump(current_frame, previous_frame, threshold):
                self._stamp_light(timestamp, annotation, subscription)
                return (True, timestamp)
            if timeout:
                if (time() - start_time > timeout):
                    print('lightstamper failed to detect a light...')
                    return (False,)
                previous_frame = current_frame
                
    def subscribe_to_camera_frames(self, subscription):
        subscriber = self.context.socket(zmq.SUB)
        subscriber.connect(
            'tcp://{}:{}'.format(self.address, self.sub_port))
        subscriber.setsockopt_string(zmq.SUBSCRIBE, subscription)
        return subscriber    

    def get_next_frame_from_worldcam(self, subscriber, subscription):
        # This assumes that we're guaranteed to get a message with
        # the subscribed topic at some point
        topic = ''
        # Would it be possible to get subscription from subscriber?
        # This way could get rid of variable "subscription"
        while topic != subscription:
            topic, msg = recv_from_subscriber(subscriber)
        recent_world = np.frombuffer(
            msg['__raw_data__'][0], dtype=np.uint8).reshape(
                msg['height'], msg['width'], 3)
        recent_world_ts = msg['timestamp']
        return recent_world, recent_world_ts
    
    def _luminance_jump(self, current_frame, previous_frame, threshold):
        return current_frame.mean() - previous_frame.mean() > threshold

    def _stamp_light(self, timestamp, annotation, subscription):
        '''Sends annotation to Pupil Capture.

        '''
        print('Light stamped on {} at {}'.format(
            subscription, timestamp))
        annotation['timestamp'] = timestamp
        self.send_annotation(annotation)

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
            
def new_annotation(label, custom_fields={}):
    '''
    Create a new annotation (a.k.a. message / event marker / whatever 
    you want to call it). Send it to Pupil Capture with the `send_annotation(...)` 
    function.

    Note
    ----
    Click `here <https://docs.pupil-labs.com/core/software/pupil-capture/#annotations>`_
    for more information on annotations.
        
    Parameters
    ----------
    label : string
        A label for the event.
    custom_fields : dict, optional
        Any additional information to add (e.g. {'duration':2, 'color':'blue'}). 
        The default is {}.

    Returns
    -------
    annotation : dict
        The annotation dictionary, ready to be sent.

    '''
    annotation = {
        'topic': 'annotation',
        'label': label,
        'timestamp': time()
        }
    for k, v in custom_fields.items():
        annotation[k] = v
    return annotation

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
