# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 11:25:53 2020

@author: engs2242
"""


"""
Receive world camera data from Pupil using ZMQ.
Make sure the frame publisher plugin is loaded and confugured to gray or rgb
"""
import zmq
import msgpack
from msgpack import unpackb, packb
import numpy as np
import threading
import restful_apy as apy


context = zmq.Context()
# open a req port to talk to pupil
addr = '127.0.0.1'  # remote ip or localhost
req_port = "50020"  # same as in the pupil remote gui
req = context.socket(zmq.REQ)
req.connect("tcp://{}:{}".format(addr, req_port))
# ask for the sub port
req.send_string('SUB_PORT')
sub_port = req.recv_string()


# send notification:
def notify(notification):
    """Sends ``notification`` to Pupil Remote"""
    topic = 'notify.' + notification['subject']
    payload = packb(notification, use_bin_type=True)
    req.send_string(topic, flags=zmq.SNDMORE)
    req.send(payload)
    return req.recv_string()


# Start frame publisher with format BGR
notify({'subject': 'start_plugin', 'name': 'Frame_Publisher', 'args': {'format': 'bgr'}})

# open a sub port to listen to pupil
sub = context.socket(zmq.SUB)
sub.connect("tcp://{}:{}".format(addr, sub_port))

# set subscriptions to topics
# recv just pupil/gaze/notifications
sub.setsockopt_string(zmq.SUBSCRIBE, 'frame.')


def recv_from_sub():
    '''Recv a message with topic, payload.
    Topic is a utf-8 encoded string. Returned as unicode object.
    Payload is a msgpack serialized dict. Returned as a python dict.
    Any addional message frames will be added as a list
    in the payload dict with key: '__raw_data__' .
    '''
    topic = sub.recv_string()
    payload = unpackb(sub.recv(), encoding='utf-8')
    extra_frames = []
    while sub.get(zmq.RCVMORE):
        extra_frames.append(sub.recv())
    if extra_frames:
        payload['__raw_data__'] = extra_frames
    return topic, payload


def send_trigger(trigger):
    payload = msgpack.dumps(trigger, use_bin_type=True)
    pub_socket.send_string(trigger["topic"], flags=zmq.SNDMORE)
    pub_socket.send(payload)
        
def detect_light_onset(trigger):
    recent_world = None
    recent_world_m1 = None
    recent_world_ts = None
    detected = False
    while not detected:
        topic, msg = recv_from_sub()
        if topic == 'frame.world':
            recent_world = np.frombuffer(msg['__raw_data__'][0], dtype=np.uint8).reshape(msg['height'], msg['width'], 3)
            recent_world_ts = msg['timestamp']
        if recent_world is not None and recent_world_m1 is not None:
            diff = recent_world.mean() - recent_world_m1.mean()
            print(recent_world_ts, recent_world.mean())
            if diff > 20:
                print("Light detected at {}".format(recent_world_ts))
                send_trigger(trigger)
                break
        recent_world_m1 = recent_world    
                  
                  
                        #print("Light detected at: {}".format(recent_world_ts))
            #print(recent_world_ts, recent_world.mean())

def new_trigger(label, duration, ts):
    return {
        "topic": "annotation",
        "label": label,
        "timestamp": ts,
        "duration": duration
    }

spectrum     = [1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000]
spectrum_off = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# set up device
device = apy.setup_device(username='admin', identity=1, password='83e47941d9e930f6')

        
for i in range(10):
    t = threading.Thread(target=detect_light_onset)
    t.start()
    apy.set_spectrum_a(device, spectrum)
    