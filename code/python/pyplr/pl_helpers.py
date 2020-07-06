# -*- coding: utf-8 -*-
'''
Created on Wed Jun 17 15:21:46 2020

@author: engs2242
'''
from time import time

import numpy as np
import msgpack
import zmq

def notify(pupil_remote, notification):
    '''
    Sends a notification to Pupil Remote.

    Parameters
    ----------
    pupil_remote : TYPE
        the pupil remote helper.
    notification : dict
        
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
    Send an annotation (a.k.a 'trigger') to Pupil Capture. 
    
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
    
def new_trigger(label, duration, custom_fields={}):
    return {
        'topic': 'annotation',
        'label': label,
        'timestamp': time(),
        'duration': duration
    }

def recv_from_subscriber(subscriber):
    '''
    Receive a message with topic and payload.
    
    Parameters
    ----------
    subscriber : zmq.sugar.socket.Socket
        a subscriber to any valid topic

    Returns
    -------
    topic : str
        a utf-8 encoded string, returned as a unicode object.
    payload : dict
        a msgpack serialized dictionary, returned as a python dictionary.
        Any addional message frames will be added as a list in the payload 
        dictionary with key: '__raw_data__'. To make useable, say: 
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

def detect_light_onset(subscriber, pub_socket, trigger, threshold, wait_time):
    '''
    Use the Pupil Core World Camera to detect the onset of a light and send 
    an annotation (a.k.a 'trigger') to Pupil Capture with the associated 
    Pupil timestamp.

    Parameters
    ----------
    subscriber : zmq.sugar.socket.Socket
        a socket subscribed to 'frame.world' 
    pub_socket : zmq.sugar.socket.Socket
        a socket to publish the trigger using send_trigger(...)
    trigger : dict
        a dictionary with at least the following:
            
        {'topic': 'annotation',
         'label': 'our_label',
         'timestamp': None}
        
        timestamp will be overwritten with the new pupil timestamp for the 
        detected light. See new_trigger(label, duration)
    threshold : int
        detection threshold for luminance increase. The right value depends on
        the nature of the light stimulus and the ambient lighting conditions. 
        Requires some guesswork right now, but it would be good to have a 
        function that works it out for us. 

    Returns
    -------
    None.

    '''
    recent_world = None
    recent_world_minus_one = None
    recent_world_ts = None
    detected = False
    print('Waiting for the light...')
    t1 = time()
    t2 = time()
    while detected == False or (t2 - t1) < wait_time:
        topic, msg = recv_from_subscriber(subscriber)
        if topic == 'frame.world':
            recent_world = np.frombuffer(msg['__raw_data__'][0], dtype=np.uint8).reshape(
                msg['height'], msg['width'], 3)
            recent_world_ts = msg['timestamp']
        if recent_world is not None and recent_world_minus_one is not None:
            diff = recent_world.mean() - recent_world_minus_one.mean()
            print(diff)
            if diff > threshold:
                print('Light change detected at {}'.format(recent_world_ts))
                trigger['timestamp'] = recent_world_ts # change trigger timestamp
                send_trigger(pub_socket, trigger)
                detected = True
                break
        recent_world_minus_one = recent_world
        t2 = time()

# def find_threshold():
# while True:
#     topic, msg = recv_from_subscriber(subscriber)
#     recent_world = np.frombuffer(msg['__raw_data__'][0], dtype=np.uint8).reshape(msg['height'], msg['width'], 3)
#     print(recent_world)