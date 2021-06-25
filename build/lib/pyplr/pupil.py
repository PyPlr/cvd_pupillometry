#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
pyplr.pupil
===========

A module for interfacing with a Pupil Core eye tracker.

@author: jtm

'''

from time import time
from concurrent import futures

import numpy as np
import msgpack
import zmq

class PupilCore:
    '''Class to facilitate working with Pupil Core via the Network API.
    
    Example
    -------
    >>> p = PupilCore()
    >>> p.command('R my_recording')
    >>> sleep(2.)
    >>> p.command('r')
    
    '''
    
    def __init__(self, address='127.0.0.1', request_port='50020', 
                 pyplr_defaults=False):
        '''Initialize the connection with Pupil Core.
        
        Parameters
        ----------
        address : string, optional
            The IP address of the device. The default is `127.0.0.1`.
        request_port : string, optional
            Pupil Remote accepts requests via a REP socket, by default on port 
            50020. Alternatively, you can set a custom port in Pupil Capture 
            or via the `--port` application argument. The default is `50020`.
        pyplr_defaults : bool, optional
            Whether to configure Pupil Capture with the defaults used for the
            ``light_stamper(...)`` method. This includes making sure the 
            Annotation Capture plugin is active, that frames are published in 
            BGR format, and that the world camera is using a frame rate of 
            (320,240) at 120 hz with exposure mode set to manual. Always 
            manually verify that the settings are appropriate for the 
            application you are running. The default is True. 
            
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
        
        # TODO: just get reid of these
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
        Send a command via `Pupil Remote 
        <https://docs.pupil-labs.com/developer/core/network-api/#pupil-remote>`_.
   
        Parameters
        ----------
        cmd : string
            Must be one of the following:
                
                * 'R'        - start recording with auto generated session name
                * 'R my_rec' - start recording named `my_rec` 
                * 'r'        - stop recording
                * 'C'        - start currently selected calibration
                * 'c'        - stop currently selected calibration
                * 'T 123.45' - resets current Pupil time to given timestamp
                * 't'        - get current Pupil time; returns a float as string
                * 'v'        - get the Pupil Core software version string
                * 'PUB_PORT' - return the current pub port of the IPC Backbone 
                * 'SUB_PORT' - return the current sub port of the IPC Backbone

        Returns
        -------
        string
            The result of the command. If the command was not acceptable, this
            will be 'Unknown command.'

        '''
        self.remote.send_string(cmd)
        return self.remote.recv_string()
   
    def notify(self, notification):
        '''Send a `notification <https://docs.pupil-labs.com/developer/core/network-api/#notification-message>`_
        to Pupil Remote. 
        
        Every notification has a topic and can contain potential payload data. 
        The payload data has to be serializable, so not every Python object 
        will work. To find out which plugins send and receive notifications, 
        open the codebase and search for ``.notify_all(`` and ``def on_notify(``. 
        
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
    
    def annotation_capture_plugin(self, should):
        '''Start or stop the Annotatiob Capture plugin.

        Parameters
        ----------
        should : str
            Either 'start' or 'stop'.

        Raises
        ------
        ValueError
            If `should` not `start` or `stop`.

        Returns
        -------
        None.

        '''
        if should not in ['start', 'stop']:
            raise ValueError('Must specify start or stop for should.')
        subject = '{}_plugin'.format(should)
        return self.notify({
            'subject': subject,
            'name': 'Annotation_Capture',
            'args': {}
            })
    
    #TODO: is this correct?
    def get_corrected_pupil_time(self):
        '''Get the current Pupil Timestamp, corrected for transmission delay.
        
        Returns
        -------
        float
            The current pupil time.
        '''
        t_before = time()
        t = float(self.command('t'))
        t_after = time()
        delay = (t_after - t_before) / 2.0
        return t + delay
    
    def _broadcast_pupil_detector_properties(self, detector_name, eye_id):
        '''Request property broadcast from a single pupil detector running in 
        single eye process.

        Parameters
        ----------
        detector_name : string
            `'Detector2DPlugin'` or `'Pye3DPlugin'`.
        eye_id : int
            For the left (0) or right(1) eye.

        Returns
        -------
        None.

        '''
        payload = {
            "subject": "pupil_detector.broadcast_properties",
            "eye_id": eye_id,
            "detector_plugin_class_name": detector_name,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        self.notify(payload)
        
    def get_pupil_detector_properties(self, detector_name, eye_id):
        '''Get the detector properties for a single pupil detector running in
        a single eye process.
        

        Parameters
        ----------
        detector_name : string
            `'Detector2DPlugin'` or `'Pye3DPlugin'`.
        eye_id : int
            For the left (0) or right(1) eye.

        Returns
        -------
        payload : dict
            Dictionary of detector properties.

        '''
        self._broadcast_pupil_detector_properties(detector_name, eye_id)
        subscriber = self.subscribe_to_topic(
            topic='notify.pupil_detector.properties')
        topic, payload = self.recv_from_subscriber(subscriber)
        return payload
    
    def freeze_3d_model(self, eye_id, frozen):
        '''Freeze or unfreeze the Pye3D pupil detector model. 
        
        The Pye3D pupil detector updates continuously unless the model is 
        frozen. The updates help to account for head slippage, but can cause 
        artefacts in the pupil data. If there is unlikely to be any slippage 
        (e.g.., the participant is using a chinrest) then it makes sense to 
        freeze the 3D model before presenting stimuli.

        Parameters
        ----------
        eye_id : int
            Whether to freeze the model for the left (1) or right (0) eye.
        frozen : bool 
            Whether to freeze or unfreeze the model.

        Raises
        ------
        ValueError
            If eye_id is not specified correctly.

        Returns
        -------
        string
            The notification response.

        '''
        if eye_id not in [0, 1]:
            raise ValueError('Must specify 0 or 1 for eye_id')
            
        if not type(frozen) == bool:
            raise TypeError('Must specify True or False for frozen')
            
        notification = {'topic': 'notify.pupil_detector.set_properties',
                        'subject': 'pupil_detector.set_properties',
                        'values': {'is_long_term_model_frozen': frozen},
                        'eye_id': eye_id,
                        'detector_plugin_class_name': 'Pye3DPlugin'}
        mode = 'Freezing' if frozen else 'Unfreezing'
        print(f'> {mode} 3d model for eye {eye_id}')
        return self.notify(notification)
    
    def check_3d_model(self, eyes=[0,1], alert=False):
        '''Stop and ask the overseer whether the 3D model should be refit.
        
        The model is well-fit when the blue and red ellipses overlap as much
        as possible for all gaze angles and when the size of the green ellipse
        is close to that of the eye ball. Open the debug windows if in doubt.
        
        Parameters
        ----------
        eyes : list of int, optional
            Which eyes to refit. The default is [0,1].

        Returns
        -------
        None.

        '''
        if alert:
            print('\a')
        while True:
            response = input('> Refit the 3d model? [y/n]: ')
            if not response in ['y','n']:
                print("> Sorry, I didn't understand that.")
                continue
            else:
                break
        if response=='y':
            for eye in eyes:
                self.freeze_3d_model(eye_id=eye, frozen=False)
            print('> Ask the participant to roll their eyes')
            input('> Press "Enter" when ready to freeze the model: ')
            for eye in eyes:
                self.freeze_3d_model(eye_id=eye, frozen=True)
        else:
            pass        
        
    def new_annotation(self, label, custom_fields={}):
        '''Create a new `annotation <https://docs.pupil-labs.com/core/software/pupil-capture/#annotations>`_
        (a.k.a. message / event marker / whatever you want to call it). Send it
        to Pupil Capture with the ``.send_annotation(...)`` method. 
    
        Note
        ----
        The default timestamp for an annotation is the current Pupil time 
        (corrected for transmission delay) at the time of creation, but this 
        can be overridden at a later point if desired.
        
        Parameters
        ----------
        label : string
            A label for the event.
        custom_fields : dict, optional
            Any additional information to add (e.g., ``{'duration': 2, 
            'color': 'blue'}``). 
            The default is ``{}``.
    
        Returns
        -------
        annotation : dict
            The annotation dictionary, ready to be sent.
    
        '''
        annotation = {
            'topic': 'annotation',
            'label': label,
            'timestamp': self.get_corrected_pupil_time()
            }
        for k, v in custom_fields.items():
            annotation[k] = v
        return annotation
    
    def send_annotation(self, annotation):
        '''Send an annotation to Pupil Capture. 
        
        Use to mark the timing of events.
        
        Parameters
        ----------
        annotation : dict
            Customiseable - see the ``.new_annotation(...)`` method.
        
        Returns
        -------
        None.
     
        '''
        payload = msgpack.dumps(annotation, use_bin_type=True)
        self.pub_socket.send_string(annotation['topic'], flags=zmq.SNDMORE)
        self.pub_socket.send(payload)
        
    def pupil_grabber(self, topic, seconds):
        '''Concurrent access to data from Pupil Core.
        
        Executes the ``.grab_data(...)`` method in a thread using
        ``concurrent.futures.ThreadPoolExecutor()``, returning a Future object
        with access to the return value.
        
        Parameters
        ----------
        topic : string
            See ``.grab_data(...)`` for more info.
        seconds : float
            Ammount of time to spend grabbing data. 

        Example
        -------
        >>> p = PupilCore()
        >>> seconds = 10.
        >>> pgr_future = p.pupil_grabber(topic='pupil.0.3d', seconds=seconds)
        >>> sleep(seconds)
        >>> data = pgr_future.result()
        
        Returns
        -------
        concurrent.futures._base_Future
            An object giving access to the data from the thread.

        '''
        args = (topic, seconds)
        return futures.ThreadPoolExecutor().submit(self.grab_data, *args)
       
    def grab_data(self, topic, seconds):
        '''Start grabbing data in real time from Pupil Core.
        
        Parameters
        ----------
        topic : string
            Subscription topic. Can be:
                
                * 'pupil.0.2d'  - 2d pupil datum (left)
                * 'pupil.1.2d'  - 2d pupil datum (right)  
                * 'pupil.0.3d'  - 3d pupil datum (left)
                * 'pupil.1.3d'  - 3d pupil datum (right)  
                * 'gaze.3d.1.'  - monocular gaze datum
                * 'gaze.3d.01.' - binocular gaze datum
                * 'logging'     - logging data
                
        seconds : float
            Ammount of time to spend grabbing data. 

        Returns
        -------
        data : list
            A list of dictionaries.

        '''
        print('> Grabbing {} seconds of {}'.format(seconds, topic))
        subscriber = self.subscribe_to_topic(topic)
        data = []
        start_time = time()
        while (time() - start_time < seconds):
            target, message = self.recv_from_subscriber(subscriber)
            data.append(message)
        print('> PupilGrabber done grabbing {} seconds of {}'.format(
                seconds, topic))
        return data
    
    def light_stamper(self, annotation, timeout, threshold=15,
                     topic='frame.world'):
        '''Concurrent timestamping of light stimuli with World Camera.
                
        Executes the ``.detect_light_onset(...)`` method in a thread using
        ``concurrent.futures.ThreadPoolExecutor()``, returning a Future object
        with access to the return value.
        
        Parameters
        ----------
        annotation : dict
        timeout : float, optional
        threshold : int
        topic : string
        
        See ``.detect_light_onset(...)`` for more information on parameters.
            
        Example
        -------
        >>> annotation = new_annotation(label='LIGHT_ON')
        >>> p = PupilCore()
        >>> p.command('R')
        >>> sleep(2.)
        >>> lst_future = p.light_stamper(annotation, threshold=15, timeout=10)
        >>> sleep(10)
        >>> # light stimulus here
        >>> p.command('r')
        >>> data = lst_future.result()
        
        Note
        ----
        Requires a suitable geometry and for the World Camera to be pointed at 
        the light source. Also requires the following settings in Pupil Capture:
            
        * Auto Exposure mode - Manual Exposure (eye and world)
        * Frame publisher format - BGR
        
        Returns
        -------
        concurrent.futures._base_Future
            An object giving access to the data from the thread.

        '''
        args = (annotation, threshold, timeout, topic)
        return futures.ThreadPoolExecutor().submit(
            self.detect_light_onset, *args)
    
    # TODO: Add option to stamp offset
    def detect_light_onset(self, annotation, timeout, threshold=15,
                           topic='frame.world'):
        '''Algorithm to detect onset of light stimulus with the World Camera.
        
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
            detected light. See ``.new_annotation(...)`` for more info.
        timeout : float
            Time to wait in seconds before giving up. For `STLAB`, use 6 s, 
            because on rare occasions it can take about 5 seconds for the 
            `LIGHT_HUB` to process a request. 
        threshold : int
            Detection threshold for luminance increase. The right value depends 
            on the nature of the light stimulus and the ambient lighting
            conditions. Requires some guesswork right now, but could easily
            write a function that works it out for us. 
        topic : string
            The camera frames to subscribe to. In most cases this will be 
            `'frame.world'`, but the method will also work for `'frame.eye.0'`
            and `'frame.eye.1'` if the light source contains enough near-
            infrared. The default is `'frame.world'`.        
        '''
        subscriber = self.subscribe_to_topic(topic)
        print('> Waiting for a light to stamp...')
        start_time = time()
        previous_frame, _ = self.get_next_camera_frame(
            subscriber, topic)
        while True:
            current_frame, timestamp = self.get_next_camera_frame(
                subscriber, topic)
            if self._luminance_jump(current_frame, previous_frame, threshold):
                self._stamp_light(timestamp, annotation, topic)
                return (True, timestamp)
            if timeout:
                if (time() - start_time > timeout):
                    print('> light_stamper failed to detect a light...')
                    return (False,)
            previous_frame = current_frame
                
    def subscribe_to_topic(self, topic):
        '''Subscribe to a topic.
        
        Parameters
        ----------
        topic : string
            The topic to which you want to subscribe, e.g., `'pupil.1.3d'`.

        Returns
        -------
        subscriber : zmq.sugar.socket.Socket
            Subscriber socket.

        '''
        subscriber = self.context.socket(zmq.SUB)
        subscriber.connect(
            'tcp://{}:{}'.format(self.address, self.sub_port))
        subscriber.setsockopt_string(zmq.SUBSCRIBE, topic)
        return subscriber    

    def get_next_camera_frame(self, subscriber, topic):
        '''Get the next camera frame. 
        
        Used by ``.detect_light_onset(...)``.

        Parameters
        ----------
        subscriber : zmq.sugar.socket.Socket
            Subscriber to camera frames.
        topic : string
            Topic string.

        Returns
        -------
        recent_frame : numpy.ndarray
            The camera frame.
        recent_frame_ts : float
            Timestamp of the camera frame.

        '''
        target = ''
        while target != topic:
            target, msg = self.recv_from_subscriber(subscriber)
        recent_frame = np.frombuffer(
            msg['__raw_data__'][0], dtype=np.uint8).reshape(
                msg['height'], msg['width'], 3)
        recent_frame_ts = msg['timestamp']
        return recent_frame, recent_frame_ts

    def recv_from_subscriber(self, subscriber):
        '''Receive a message with topic and payload.
        
        Parameters
        ----------
        subscriber : zmq.sugar.socket.Socket
            A subscriber to any valid topic.
            
        Returns
        -------
        topic : str
            A utf-8 encoded string, returned as a unicode object.
        payload : dict
            A msgpack serialized dictionary, returned as a python dictionary.
            Any addional message frames will be added as a list in the payload 
            dictionary with key: ``'__raw_data__'``. 
            
        '''
        topic = subscriber.recv_string()
        payload = msgpack.unpackb(subscriber.recv())
        extra_frames = []
        while subscriber.get(zmq.RCVMORE):
            extra_frames.append(subscriber.recv())
        if extra_frames:
            payload['__raw_data__'] = extra_frames
        return topic, payload   

    def fixation_trigger(self, max_dispersion=3.0, min_duration=300, 
                         trigger_region=[0.0, 0.0, 1.0, 1.0]):
        '''Wait for a fixation that satisfies the given constraints. 
        
        Use to check for stable fixation before presenting a stimulus, for
        example.
        
        Note
        ----
        Uses real-time data published by Pupil Capture's `Online Fixation 
        Detector Plugin
        <https://docs.pupil-labs.com/developer/core/network-api/#fixation-messages>`_
                
        Parameters
        ----------
        max_dispersion : float, optional
            Maximum dispersion threshold in degrees of visual angle. In other
            words, how much spatial movement is allowed within a fixation? 
            Pupil Capture allows manual selection of values from `0.01` to 
            `4.91`. The default is `3.0`.
        min_duration : int, optional
            Minimum duration threshold in milliseconds. In other words, what is
            the minimum time required for gaze data to be within the dispersion
            threshold? Pupil Capture allows manual selection of values from 
            `10` to `4000`. The default is `300`.
        trigger_region : list, optional
            World coordinates within which the fixation must fall to be valid.
            The default is ``[0.0, 0.0, 1.0, 1.0]``, which corresponds to the
            whole camera scene in normalised coordinates.

        Returns
        -------
        fixation : dict
            The triggering fixation.

        '''
        self.notify({
            'subject': 'start_plugin',
            'name': 'Fixation_Detector',
            'args': {'max_dispersion': max_dispersion,
                     'min_duration': min_duration}
            }) 
        s = self.subscribe_to_topic(topic='fixation')
        print('> Waiting for a fixation...')
        while True:
            topic, fixation = self.recv_from_subscriber(s)
            if self._fixation_in_trigger_region(fixation, trigger_region):
                print('> Valid fixation detected...')
                return fixation
            
    def _fixation_in_trigger_region(self, fixation, 
                                    trigger_region=[0.0, 0.0, 1.0, 1.0]):
        '''Return True if fixation is within trigger_region else False.

        '''
        x, y = fixation['norm_pos']
        return (x > trigger_region[0] and x < trigger_region[2] 
                and y > trigger_region[1] and y < trigger_region[3])
            
    def _luminance_jump(self, current_frame, previous_frame, threshold):
        '''Detect an increase in luminance.

        '''
        return current_frame.mean() - previous_frame.mean() > threshold

    def _stamp_light(self, timestamp, annotation, subscription):
        '''Send annotation with updated timestamp.
        
        '''
        print('> Light stamped on {} at {}'.format(
            subscription, timestamp))
        annotation['timestamp'] = timestamp
        self.send_annotation(annotation)
        