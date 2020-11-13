# -*- coding: utf-8 -*-
"""
Created on Wed Jun 17 15:29:09 2020

@author: engs2242
"""
import threading
from time import time, sleep
import STLAB_apy as stlab
import pl_helpers as plh
import zmq

# make 1s pulse
stlab.make_video_pulse([4095]*10, 1000, '1s_max_pulse')

# set up zmq context and remote helper for tracker
context = zmq.Context()
address = '127.0.0.1'  # remote ip or localhost
request_port = "50020"  # same as in the pupil remote gui
pupil_remote = zmq.Socket(context, zmq.REQ)
pupil_remote.connect("tcp://{}:{}".format(address, request_port))

# Request 'SUB_PORT' for reading data
pupil_remote.send_string('SUB_PORT')
sub_port = pupil_remote.recv_string()

# Request 'PUB_PORT' for writing data
pupil_remote.send_string('PUB_PORT')
pub_port = pupil_remote.recv_string()

pub_socket = zmq.Socket(context, zmq.PUB)
pub_socket.connect("tcp://{}:{}".format(address, pub_port))

pupil_remote.send_string("T {}".format(time()))
print(pupil_remote.recv_string())

subscriber = context.socket(zmq.SUB)
subscriber.connect("tcp://{}:{}".format(address, sub_port))

# set subscriptions to topics
# recv just pupil/gaze/notifications
subscriber.setsockopt_string(zmq.SUBSCRIBE, 'frame.')
    
# setup stlab
d = stlab.Device(username='admin', identity=1, password='83e47941d9e930f6')
d.load_video_file('1s_max_pulse.dsf')

label = "LIGHT_ON"
light_on_trigger = plh.new_trigger(label, 2.)
threshold=10

# start recording
pupil_remote.send_string("R")
pupil_remote.recv_string()

sleep(5.)  

for i in range(10):
    sleep(5.)  
    t = threading.Thread(target=plh.detect_light_onset, args=(subscriber, pub_socket, light_on_trigger, threshold))
    t.start()
    sleep(.5)
    d.play_video_file()
    sleep(5.)  
    
sleep(5.)   
pupil_remote.send_string("r")
pupil_remote.recv_string()

