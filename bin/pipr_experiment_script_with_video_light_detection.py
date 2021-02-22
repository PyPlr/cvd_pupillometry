# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 11:16:51 2020

@author: -
"""
import restful_apy as apy
import zmq
import msgpack as serializer
import numpy as np
import threading
# import numpy as np

# apy.set_spectrum_a(device,red)
# red_spec = apy.get_spectrometer_spectrum(device)
# apy.set_spectrum_a(device,blue)
# blue_spec = apy.get_spectrometer_spectrum(device)
# bins = np.linspace(380,780,81)
# plt.plot(bins,red_spec, color='red')
# plt.plot(bins, blue_spec, color='blue')

if __name__ == "__main__":
    from time import sleep, time

    # set up light device
    device = apy.setup_device(username='admin', identity=1, password='83e47941d9e930f6')
    
    # red and blue lights
    blue = [0, 0, 4095, 4095, 4095, 0, 0, 0, 0, 0]
    red  = [0, 0, 0, 0, 0, 0, 0, 0, 1000, 1000]
    
    # Setup zmq context and remote helper for tracker
    context = zmq.Context()
    addr = '127.0.0.1'  # remote ip or localhost
    req_port = "50020"  # same as in the pupil remote gui
    pupil_remote = zmq.Socket(context, zmq.REQ)
    pupil_remote.connect("tcp://{}:{}".format(addr, req_port))

    pupil_remote.send_string("PUB_PORT")
    pub_port = pupil_remote.recv_string()
    pub_socket = zmq.Socket(context, zmq.PUB)
    pub_socket.connect("tcp://127.0.0.1:{}".format(pub_port))
    pupil_remote.send_string('SUB_PORT')
    sub_port = pupil_remote.recv_string()

    # In order for the annotations to be correlated correctly with the rest of
    # the data it is required to change Pupil Capture's time base to this scripts
    # clock. We only set the time base once. Consider using Pupil Time Sync for
    # a more precise and long term time synchronization
    time_fn = time  # Use the appropriate time function here

    # Set Pupil Capture's time base to this scripts time. (Shoulnd be done before
    # starting the recording)
    pupil_remote.send_string("T {}".format(time_fn()))
    print(pupil_remote.recv_string())

    # send notification:
    def notify(notification):
        """Sends ``notification`` to Pupil Remote"""
        topic = "notify." + notification["subject"]
        payload = serializer.dumps(notification, use_bin_type=True)
        pupil_remote.send_string(topic, flags=zmq.SNDMORE)
        pupil_remote.send(payload)
        return pupil_remote.recv_string()

    def send_trigger(trigger):
        payload = serializer.dumps(trigger, use_bin_type=True)
        pub_socket.send_string(trigger["topic"], flags=zmq.SNDMORE)
        pub_socket.send(payload)

    # Start the annotations plugin
    notify({"subject": "start_plugin", "name": "Annotation_Capture", "args": {}})
    #notify({"subject": "start_plugin", "name": "Time_Sync", "args": {}}) # added this...?
    
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
        payload = serializer.unpackb(sub.recv(), encoding='utf-8')
        extra_frames = []
        while sub.get(zmq.RCVMORE):
            extra_frames.append(sub.recv())
        if extra_frames:
            payload['__raw_data__'] = extra_frames
        return topic, payload

    def detect_light_onset(trigger, threshold):
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
                if diff > threshold:
                    print("Light detected at {}".format(recent_world_ts))
                    trigger['timestamp'] = recent_world_ts # change timestamp
                    send_trigger(trigger)
                    break
            recent_world_m1 = recent_world    
            
    pupil_remote.send_string("R")
    pupil_remote.recv_string()

    sleep(1.)  # sleep for a few seconds, can be less

    # Send a trigger with the current time
    # The annotation will be saved to annotation.pldata if a
    # recording is running. The Annotation_Player plugin will automatically
    # retrieve, display and export all recorded annotations.

    def new_trigger(label, duration, color):
        return {
            "topic": "annotation",
            "label": label,
            "timestamp": time_fn(),
            "duration": duration,
            "color": color
        }

    # make trigger labels
    label_on = "light_on"
    duration_on = 2.
    
    # set up trial dict
    trials = {
        '1':[red, 'red'],
        '2':[blue,'blue'],
        '3':[red,'red'],
        '4':[blue, 'blue'],
        '5':[red, 'red'],
        '6':[blue,'blue']
        }
    
    # baseline
    sleep(5.) 
    
    # run trials
    for i, trial in trials.items(): 
        sleep(5.) 
        on_trigger  = new_trigger(label_on, duration_on, trial[1]) # make on trigger
        t = threading.Thread(target=detect_light_onset, args=(on_trigger,20))
        t.start()
        sleep(1.)
        send_trigger(on_trigger)
        apy.set_spectrum_a(device, trial[0]) # turn on the light
        sleep(2.) # two second light pulse
        apy.turn_off(device) # turn off the light
        sleep(10.) # give it 10

    # stop recording
    pupil_remote.send_string("r")
    pupil_remote.recv_string()
