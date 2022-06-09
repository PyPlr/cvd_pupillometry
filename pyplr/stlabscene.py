#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stlabscene
==========

A module for launching two different video files on separate STLabs at the 
same time. Speak to Ledmotive about the scene command. 

"""

import requests

from pyplr.stlab import SpectraTuneLab, video_file_to_dict


class SpectraTuneLabScene(SpectraTuneLab):
    """Subclass of `stlab.SpectraTuneLab` with support for custom scene 
    command.

    """

    def __init__(self, password, username='admin', default_address=1,
                 lighthub_ip='192.168.7.2'):
        """See `stlab.SpectraTuneLab` for more info.

        """

        super().__init__(password, username, default_address, lighthub_ip)
        
    # TODO: can this replace load_video_file in main class? 
    # Don't think so... It is a custom command... load_video_file renaims to 
    # video1.json
    def upload_video(self, fname, return_vf_dict=True):
        """Upload a video file to the Light Hub.
        
        To achieve a good synchronization between multiple videos, when using
        the `scene` command, the first and most important optimization we can 
        perform, is to upload all the videos before we will need to reproduce 
        them in the luminaires.
        
        The video uploading follows the same process as before, but you are
        now not limited to a single video. Instead, you can now include the 
        name of the filename to use in the endpoint path, to make the uploaded 
        file take that filename in the LIGHT HUB. Only the following filenames 
        are accepted: video1.json, video2.json, video3.json, video4.json, 
        video5.json, video1.dsf, video2.dsf, video3.dsf, video4.dsf and 
        video5.dsf.
        
        This effectively means you can have up to 10 different custom videos in
        the LIGHT HUB. Each video can be up to 40 MB in size (it is advisable
        to minimize the JSON format before uploading to reduce the file size).
        In the event of an error saying the disk is full, you can try to free
        some space by uploading smaller videos to overwrite the previous ones.

        Parameters
        ----------
        fname : str
            Name of the video file to upload. Only the following filenames are 
            accepted: video1.json, video2.json, video3.json, video4.json, 
            video5.json, video1.dsf, video2.dsf, video3.dsf, video4.dsf and
            video5.dsf. This effectively means we can have up to 10 different
            custom videos in the LIGHT HUB. Each video can be up to 40 MB in 
            size (it is advisable to minimize the JSON format before uploading 
            to reduce the file size). In case you get an error saying the disk
            is full, you can try to free some space by uploading smaller videos 
            to overwrite the previous ones.
        return_vf_dict : bool, optional
            Whether to return the video file as a dict when uploaded. The 
            default is True.

        Returns
        -------
        dict if return_vf_dict is True else None

        """
        args = [('file', (fname, open(fname, 'rb'), 'application/json'))]
        cmd_url = 'http://' + self.info['url'] + ':8181/api/gateway/video/' + \
            fname
        response = requests.post(
            cmd_url, files=args, cookies=self.info['cookiejar'], verify=False)
        if 'data' not in response.json():
            raise 'Upload file error'
        print('video file loaded...')
        if return_vf_dict:
            return video_file_to_dict(fname)    
    
    def scene(
            self, 
            source_1: int,
            source_2: int, 
            source_1_vf: str, 
            source_2_vf: str, 
            source_1_delay: int = 0,
            source_2_delay: int = 0):
        """Play different video files at the same time on different luminaires. 
        
        This new command has been developed in order to achieve an even
        greater synchronization time between multiple videos. With the scene
        command you can establish what spectrum or video to play on each
        luminaire or group of luminaires with a single command, thus greatly
        reducing the uncertainties of the local network elapsed times.
        
        The command is defined as POST /api/gateway/scene and it sets the
        state of the whole network of luminaires with a single request. The 
        data passed as input defines the spectrum or video sequence for each
        luminaire or group in the network. The input data is a JSON document
        whose keys are the device addresses and their values are objects that
        define the properties to be set, the “spectrum” in particular. If an
        address is not included within the document, the spectrum of that 
        device will not be altered (i.e. you only need to include the devices 
        and properties you want to change).
        
        The “spectrum” property value must be an array with the values of the
        spectrum to set as defined for SPECTRUM_A or SPECTRUM_S, or a string
        with the name of the video to play. In the case of videos, an offset 
        can be passed in order to start them with a delay, using a list of two
        elements where the first one is the video filename and the second is
        the offset in seconds.
        
        The command has a synchronization mechanism that ensures all the
        videos launched by the scene use the same start time as a reference.
        This way, the video frames can be synchronized even if it takes a few
        milliseconds to process and set the state of each luminaire in the 
        scene. The initial frames of each video can still be impacted by this 
        different processing times. This synchronization mechanism is ignored 
        if the video header includes a value for the "startDate" entry, using 
        in that case the start date as reference (typically that day midnight,
        if our video requires synchronization with current time of the day).
        
        When using this command to start multiple videos at the same time, a
        good level of synchronization can be achieved, provided that the LIGHT
        HUB is not sending more than one spectrum frame through the data bus
        each 10 ms. The videos typical precision in the timing of each frame is
        within ±3 ms. If the LIGHT HUB cannot keep up with the rate at which
        the frames should be sent (because the video design exceeds this timing
        specifications or because the device is busy with other requested 
        tasks) intermediate frames might be skipped in order to maintain the 
        best possible synchronization.
        
        Parameters
        ----------
        source_1 : int
            Device ID or multicast address for source 1.
        source_2 : int
            Device ID or multicast address for source 2.
        source_1_vf : str
            Video file for source 1.
        source_2_vf : str
            Video file for source 2.
        source_1_delay : int
            Delay in milliseconds before the video starts on playing on source
            1. The default is 0.
        source_2_delay : int
            Delay in milliseconds before the video starts on playing on source
            2. The default is 0.  
            
        Returns
        -------
        {}
            The return is an empty document. Despite the blank response it 
            might be some states are not set because a bad input value or some 
            limitation in the device (for example sending a video designed for 
            a 7 channels device to a 10 channels device).

        """
        data = {
            'arg': {
                source_1: {'spectrum': [source_1_vf, source_1_delay]}, 
                source_2: {'spectrum': [source_2_vf, source_2_delay]}  
                }
            }
        cmd_url = 'http://' + self.info['url'] + ':8181/api/gateway/scene'
        return requests.post(
            cmd_url, json=data, cookies=self.info['cookiejar'], verify=False)
