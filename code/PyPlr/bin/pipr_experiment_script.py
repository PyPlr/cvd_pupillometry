# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 11:16:51 2020

@author: -
"""
import STLAB_apy as stlab
import zmq
import msgpack as serializer
# import numpy as np

# stlab.set_spectrum_a(device,red)
# red_spec = stlab.get_spectrometer_spectrum(device)
# stlab.set_spectrum_a(device,blue)
# blue_spec = stlab.get_spectrometer_spectrum(device)
# bins = np.linspace(380,780,81)
# plt.plot(bins,red_spec, color='red')
# plt.plot(bins, blue_spec, color='blue')

if __name__ == "__main__":
    from time import sleep, time

    # set up light device
    device = stlab.setup_device(username='admin', identity=1, password='83e47941d9e930f6')
    
    # red and blue lights
    blue = [0, 0, 4095, 4000, 1000, 0, 0, 0, 0, 0]
    red  = [0, 0, 0, 0, 0, 0, 0, 0, 4095, 4095]
    
    # Setup zmq context and remote helper for tracker
    ctx = zmq.Context()
    pupil_remote = zmq.Socket(ctx, zmq.REQ)
    pupil_remote.connect("tcp://127.0.0.1:50020")

    pupil_remote.send_string("PUB_PORT")
    pub_port = pupil_remote.recv_string()
    pub_socket = zmq.Socket(ctx, zmq.PUB)
    pub_socket.connect("tcp://127.0.0.1:{}".format(pub_port))

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
    label_off = "light_off"
    duration_on = 2.
    duration_off = 0.
    
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
    sleep(20.) 
    
    # run trials
    for i, trial in trials.items(): 
        sleep(10.) 
        on_trigger  = new_trigger(label_on, duration_on, trial[1]) # make on trigger
        send_trigger(on_trigger) # send on trigger
        stlab.set_spectrum_a(device, trial[0]) # turn on the light
        sleep(2.) # two second light pulse
        off_trigger = new_trigger(label_off, duration_off, trial[1]) # make off trigger
        send_trigger(off_trigger) # send off trigger
        stlab.turn_off(device) # turn off the light

        sleep(60.) # give it a minute

    # stop recording
    pupil_remote.send_string("r")
    pupil_remote.recv_string()

