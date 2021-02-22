# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 11:16:51 2020

@author: -
"""
import restful_apy as apy
import zmq
import msgpack as serializer
#import random

if __name__ == "__main__":
    from time import sleep, time

    # set up light device
    device = apy.setup_device(username='admin', identity=1, password='83e47941d9e930f6')
    
    # background spectrum
    bg = [204, 2047, 2047, 2047, 2047, 2047, 2047, 2047, 2047, 2047]
    
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

    # Set Pupil Capture's time base to this scripts time. (Should be done before
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

    def new_trigger(label, duration, stim):
        return {
            "topic": "annotation",
            "label": label,
            "timestamp": time_fn(),
            "duration": duration,
            "stim": stim
        }

    # video files
    trials = ["f1dur60.dsf",
              "f0.5dur60.dsf",
              "f0.05dur60.dsf"]
    trials = trials*2
    
    # make trigger labels
    label_start = "video_start"
    label_stop = "video_stop"
    label_mod = "modulation_start"
    video_dur = 70
    mod_dur = 60
    duration_off = 0.
    
    # baseline
    sleep(10.) 
    
    # run trials
    for i, trial in enumerate(trials):
        print(trial)
        #adapt to background spectrum before first trial
        if i == 0:
            apy.set_spectrum_a(device, bg)
            sleep(10.)
            
        apy.load_video_file(device, trial)
        sleep(5.) 
        t1 = time()
        on_trigger   = new_trigger(label_start, video_dur, trial) # make on trigger
        send_trigger(on_trigger) # send on trigger
        apy.play_video_file(device)
        t2 = time()
        sleep(10. - (t2-t1))
        mod_trigger  = new_trigger(label_mod, mod_dur, trial) # make mod start trigger
        send_trigger(mod_trigger) # send mod start trigger
        sleep(60)
        off_trigger  = new_trigger(label_stop, duration_off, trial) # make off trigger
        send_trigger(off_trigger) # send off trigger
        sleep(5.) 


    # stop recording
    pupil_remote.send_string("r")
    pupil_remote.recv_string()
