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
    '''Subclass of `stlab.SpectraTuneLab` with support for custom scene 
    command.

    '''

    def __init__(self, password, username='admin', identity=1,
                 lighthub_ip='192.168.7.2'):
        '''See `stlab.SpectraTuneLab` for more info.

        '''

        super().__init__(password, username, identity, lighthub_ip)
        
    # TODO: can this replace load_video_file in main class? 
    def upload_video(self, fname, return_vf_dict=True):
        '''Upload a video file to the Light Hub.

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

        Raises
        ------
        
            DESCRIPTION.

        Returns
        -------
        dict if return_vf_dict is True else None

        '''
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
        '''Custom command to launch two different video files at the same time 
        on different luminaires. 
        
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

        '''
        data = {
            'arg': {
                source_1: {'spectrum': [source_1_vf, source_1_delay]}, 
                source_2: {'spectrum': [source_2_vf, source_2_delay]}  
                }
            }
        cmd_url = 'http://' + self.info['url'] + ':8181/api/gateway/scene'
        return requests.post(
            cmd_url, json=data, cookies=self.info['cookiejar'], verify=False)
