#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  5 11:40:12 2021

@author: jtm545
"""

import requests

from pyplr.stlab import SpectraTuneLab, pulse_protocol, video_file_to_dict


class SpectraTuneLabScene(SpectraTuneLab):
    '''Subclass of `stlab.SpectraTuneLab` with support for custom scene 
    command.

    '''

    def __init__(self, password, username='admin', identity=1,
                 lighthub_ip='192.168.7.2'):
        '''Initialize class and subclass. See `pyplr.stlab.SpectraTuneLab` for
        more info.

        Parameters
        ----------
        external : Class, optional
            Acquire concurrent measurements with an external spectrometer.
            Must be a device class with ``.measurement(...)`` and
            ``.wavelengths(...)`` methods. See `pyplr.oceanops.OceanOptics`
            for an example.

        Returns
        -------
        None.

        '''

        super().__init__(password, username, identity, lighthub_ip)
        
    def load_video_file_2(self, fname, return_vf_dict=True):
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
    
    def preload_video_files():
        pass
    
    def scene(self, source1, source2):
        data = {
            'arg': {
                source1: {'spectrum': ['video1.dsf', 0]}, #  added zero here for no delay 
                source2: {'spectrum': ['video2.dsf', 0]}  #  added zero here for no delay 
                }
            }
        cmd_url = 'http://' + self.info['url'] + ':8181/api/gateway/scene'
        return requests.post(
            cmd_url, json=data, cookies=self.info['cookiejar'], verify=False)

d = SpectraTuneLabScene(password='23acd0c3e4c5c533', identity=1, lighthub_ip='192.168.6.2')
d.load_video_file_2('video1.dsf')
d.load_video_file_2('video2.dsf')
d.get_video_file_metadata('video1.dsf')
d.get_video_file_metadata('video2.dsf')
d.scene(1,2)
