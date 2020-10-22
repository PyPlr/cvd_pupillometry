# -*- coding: utf-8 -*-
'''
Created on Thu Mar 26 09:20:38 2020

@author: - JTM

A python wrapper for most of the ledmotive RESTful API. 
See the "LIGHT HUB RESTful API" manual for further functions and more info.

Contains additional functions for working with the STLAB.
'''

from time import sleep
from datetime import datetime
from random import shuffle
import json

import requests
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pyplr.oceanops import adaptive_measurement

##########################
# Device class for STLAB #
##########################

class STLAB():
    '''
    A class to encapsulate the LEDMOTIVE Spectra Tune Lab device and its 
    RESTFUL_API. 
    
    Attributes
    ----------
    description : string
        A description of the device.
    colors : string
        Closest Matplotlib colornames for the 10 channels.
    rgb_colors : list
        rgb colors of the 10 channels
    wlbins : list
        The wavelengths output by the on-board spectrometer
    min_intensity : int
        The minimum intensity setting for LEDs
    max_intensity : int
        The maximum intensity setting for the LEDs
    
    '''
    # Class attributes
    description = 'Spectrally tuneable light engine with 10 narrow-band primaries'
    colors = ['blueviolet', 'royalblue', 'darkblue', 'blue', 'cyan', 
              'green', 'lime', 'orange', 'red', 'darkred']
    rgb_colors = [[.220, .004, .773, 1.], [.095, .232, .808, 1.],
                  [.098, .241, .822, 1.], [.114, .401, .755, 1.],
                  [.194, .792, .639, 1.], [.215, .895, .489, 1.],
                  [.599, .790, .125, 1.], [.980, .580, .005, 1.],
                  [.975, .181, .174, 1.], [.692, .117, .092, 1.]]
    
    wlbins = [int(val) for val in np.linspace(380, 780, 81)]
    min_intensity = 0
    max_intensity = 4095

    # Initializer / Instance Attributes
    def __init__(self, username, identity, password, lighthub_ip='192.168.7.2'):
        '''
        Initialize connection with LightHub. 
        
        Parameters
        ----------
        username : string
            The username for logging in. 
        identity : int
            A unique numerical identifier for the device. 
        password : string
            The password specific to the device.
        lightub_ip : string, optional
            The IP address of the LightHub device. The Mac connection driver 
            usually creates the network in a way that places the LightHub 
            device at IP 192.168.6.2 instead of IP 192.168.7.2, so this may need
            to be changed depending on the platform. If that is not enought, 
            you might need to also install the two Mac OX drivers required by 
            the beagleboard (the LightHub motherboard):
            Network: https://beagleboard.org/static/Drivers/MacOSX/RNDIS/HoRNDIS.pkg
            Serial: https://beagleboard.org/static/Drivers/MacOSX/FTDI/EnergiaFTDIDrivers2.2.18.pkg
            The default is '192.168.7.2'.

        Returns
        -------
        None.

        '''
        self.username = username
        self.identity = identity
        self.password = password
        self.info = None
        
        try:
            cmd_url = 'http://' + lighthub_ip + ':8181/api/login'
            a = requests.post(cmd_url, 
                              json={'username' : username,
                                    'password' : password}, 
                              verify=False)
            cookiejar = a.cookies
            sleep(.1)
            self.info = {
                'url' : lighthub_ip,
                'id' : identity,
                'cookiejar' : cookiejar
                }
            more_info = self.get_device_info()
            self.info = {**self.info, **more_info}
            # for some reason, after first turning on the STLAB, video files 
            # won't play unless you first do something in synchronous mode. A 
            # quick call to spectruma at startup gets around this issue, but 
            # it might be a good idea to ask Ledmotive about this. Also, the
            # first time you do play a video file, it often flickers.
            self.spectruma([0,0,0,0,0,0,0,0,10,10]) 
            sleep(.2)
            self.turn_off()
            print('STLAB device setup complete...')
            
        except requests.RequestException as err:
            print('login error: ', err)
        
    # Functions wrapped from STLAB's RESTFUL_API (incuding relevant documentation)
    def set_spectrum_a(self, intensity_values):
        '''
        Executes a spectrum based on the intensity values provided for each of the 
        channels. Each channel can be set between 0 and 4095 (only integer values).
    
        Parameters
        ----------
        intensity_values : list
            list of 10 integer values between 0 and 4095
    
        Returns
        -------
        None.
        
        '''
        data = {'arg' : intensity_values}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            str(self.info['id']) + '/command/SET_SPECTRUM_A'
        requests.post(cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)
    
    def set_spectrum_s(self, spectrum):
        '''
        Executes the given spectrum. The spectrum is defined by an array of 
        81 elements that represents 5 nm wavelength bins from 380 nm to 780 nm.
        The values are an abstraction of the light intensity at each point 
        that allows the reconstruction of the spectrum shape. Each value ranges 
        between 0 and 65535, being 0 no intensity and 65535 full intensity at 
        the corresponding wavelength bin (prior application of dimming and 
        power protection caps).

        Parameters
        ----------
        spectrum : list
            list of 81 (the 380 nm to 780 nm bins) integer values between 
            0 and 65535.

        Returns
        -------
        None.

        '''
        data = {'arg' : spectrum}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            str(self.info['id']) + '/command/SET_SPECTRUM_S'
        requests.post(cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)
        
    def spectruma(self, intensity_values):
        '''
        Executes a spectrum based on the intensity values provided for each of
        the channels. Each channel can be set between 0 and 4095. This is an 
        alternative way to the command SET_SPECTRUM_A that allows setting a 
        spectrum issuing a GET command (which allows access to the luminaire by
        typing a url in any browser). 
        
        Parameters
        ----------
        intensity_values : list
            list of 10 integer values between 0 and 4095.
    
        Returns
        -------
        None.
        
        '''
        spec = ''.join([str(val) + ',' for val in intensity_values])[:-1]
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            str(self.info['id']) + '/spectruma/' + spec
        requests.get(cmd_url, cookies=self.info['cookiejar'], verify=False)
    
    def color_xy(self, intensity_values, x, y):
        '''
        Similar to the 'spectruma' command, but allows setting a target x, y
        coordinates in the CIE1931 color space. 
    
        Parameters
        ----------
        intensity_values : list
            the desired spectrum as a list of integers.
        x : float
            desired target CIE1931 x coordinate as a decimal number.
        y : float
            desired target CIE1931 y coordinate as a decimal number.
    
        Returns
        -------
        None.
        
        '''
        spec = ''.join([str(val) + ',' for val in intensity_values])[:-1]
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            str(self.info['id']) + '/spectruma/' + spec + '/color/' + \
                str(x) + '/' + str(y)
        requests.get(cmd_url, cookies=self.info['cookiejar'], verify=False)

    def set_color(self, x, y, flux=None):
        '''
        Executes a light color represented in the CIE1931 color space. The x and y
        coordinates are the mathematical index that represents the target color to 
        be achieved. If the x,y provided values are not available by the system, 
        it will find its nearest available x,y coordinates. If flux is provided as
        an argument, it will be adjusted automatically, otherwise the current flux 
        will be used. 
    
        Parameters
        ----------
        x : float
            desired target CIE1931 x coordinate as a decimal number.
        y : float
            desired target CIE1931 y coordinate as a decimal number.
        flux : int, optional
            value between 0 and 4095. The default is None.
    
        Returns
        -------
        None.
        
        '''
        if flux:
            data = {'arg':[x, y, flux]}
        else:
            data = {'arg':[x, y]}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            str(self.info['id']) + '/command/SET_COLOR'
        requests.post(cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)
    
    def turn_off(self):
        '''
        Stops light emission by setting the power at all channels to 0.   
        
        Parameters
        ----------
        None.
    
        Returns
        -------
        None.
        
        '''
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            str(self.info['id']) + '/command/TURN_OFF'
        requests.post(cmd_url, cookies=self.info['cookiejar'], verify=False) 
    
    def set_blink(self, blink=1):
        '''
        Commands the luminaire to blink. The value provided as an argument is the
        number of times the light blinks in one second.
    
        Parameters
        ----------
        blink : int, optional
            number of times the light should blink in one second. The default is 1.
    
        Returns
        -------
        None.
        
        '''
        data = {'arg':blink}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            str(self.info['id']) + '/command/SET_BLINK'
        requests.post(cmd_url, cookies=self.info['cookiejar'], json=data, verify=False) 
  
    def get_pcb_temperature(self):
        '''
        Returns the PCB temperature in Celsius degrees (ºC). Returns a list of 
        4 elements in this order: LEDs, Drivers, Spectrometer and Microcontroller 
        temperature sensors close to these elements. If one sensor or its readout 
        is not available a null value is returned for that element. 
        
        Parameters
        ----------
        None.
    
        Returns
        -------
        temperatures : np.array
            [  Number,  Number,  Number,  Number  ].
            
        '''
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            str(self.info['id']) + '/command/GET_PCB_TEMPERATURE'
        r = requests.get(cmd_url, cookies=self.info['cookiejar'], verify=False)
        temperatures = dict(r.json())['data']
        return temperatures
    
    def get_spectrum_a(self):
        '''
        Returns the current amplitude for each of the luminaire channels. The 
        array returned has a length equal to the channel count of the luminaire. 
        Each value in the array is a representation of electrical counts, 
        ranging from 0 to 4095 counts.

        Returns
        -------
        None.

        '''
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            str(self.info['id']) + '/command/GET_SPECTRUM_A'
        r = requests.get(cmd_url, cookies=self.info['cookiejar'], verify=False) 
        spectrum = np.array(dict(r.json())['data'][1:])
        return spectrum
     
    def get_spectrometer_spectrum(self, norm=False):
        '''
        Returns the spectrum readout from the internal spectrometer. If the
        luminaire does only contain a colorimeter sensor, a theoretical spectrum 
        based on the current channels power is obtained instead. 
        The data is returned in 81 elements that represents a 5 nm wavelength 
        bins from 380 nm to 780 nm. Each element is a value ranging from 0 to 
        65535 abstracting the light intensity at each point and allowing the 
        reconstruction of the spectral shape. An additional element represents
        the radiometric value in milliWatts (mW) at the peak of a max value of 
        a spectrum at which the abstracted values are normalized, i.e. the flux
        corresponding to a 65535 value in the array. This flux depends on multiple
        factors, as current channels power, dimming level, power protection and 
        maximum power of the lighted LEDs.     
    
        Parameters
        ----------
        norm : bool, optional
            whether to normalize the spectrum to its peak radiometric value
    
        Returns
        -------
        spectrum : list
            [Number, Number, ..., Number, Number] with 81 elements
            
        '''
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            str(self.info['id']) + '/command/GET_SPECTROMETER_SPECTRUM'
        r = requests.get(cmd_url, cookies=self.info['cookiejar'], verify=False) 
        rmv = dict(r.json())['data'][0]
        spectrum = np.array(dict(r.json())['data'][1:])
        if norm:
            return rmv, spectrum
        else:
            return rmv, spectrum * rmv
    
    def get_led_calibration(self):
        '''
        Returns the current LED calibration matrix containing 10 rows 
        (for each channel) and 81 columns (intensity value from 380 to 780 nm 
        in steps of 5 nm).     
    
        Parameters
        ----------
        None.
        
        Returns
        -------
        matrix : list
            10 x 81 calibration matrix.
            
        '''
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            str(self.info['id']) + '/command/GET_LED_CALIBRATION'
        r = requests.get(cmd_url, cookies=self.info['cookiejar'], verify=False)   
        matrix = dict(r.json())['data'] 
        return matrix
        
    def load_video_file(self, video):
        '''
        Uploads a video light sequence file to the LIGHT HUB. The video file 
        must follow the LEDMOTIVE Dynamic Sequence File (.dsf) format. The 
        uploaded file must be a json file (.dsf files are json files), and 
        weight less than 2 MB. The file must be uploaded using the multipart / 
        form-data standard convention. See play_video_file later about how 
        to play the uploaded file in a luminaire.  
    
        Parameters
        ----------
        video : string
            name of the video file.
    
        Returns
        -------
        None.
        
        '''
        args = [('file', (video, open(video, 'rb'), 'application/json'))]
        cmd_url = 'http://' + self.info['url'] + ':8181/api/gateway/video' 
        r = requests.post(cmd_url, files=args, cookies=self.info['cookiejar'], verify=False)
        if 'data' not in r.json():
            raise 'Upload file error'
        print('video file loaded...')
        
    def play_video_file(self, stop=False):
        '''
        Starts the execution of a light video sequence in the specified luminaire
        or multicast address. If no video is in the LIGHT HUB, an error response
        is raised, and the command ignored. If the video is already playing, the 
        play is interrupted, and the video is reproduced back from the beginning. 
        To stop the video, set 'stop' to True. See load_video_file for how to
        load a video file. 
    
        Parameters
        ----------
        stop : bool, optional
            whether the command should stop the video. The default is False.
    
        Returns
        -------
        None.

        '''
        if stop:
            data = {'arg': None}
        else:
            data = {'arg': './data/video1.json'}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            str(self.info['id']) + '/command/PLAY_VIDEO_FILE'
        requests.post(cmd_url, json=data, cookies=self.info['cookiejar'], verify=False)
        print('playing video file...')
        
    def get_device_info(self):
        '''
        Returns the device characteristics and basic configuration. These are 
        the serial code, the model code, the number of channels for this 
        luminaire and the device feedback type (whether it is colorimeter or 
        spectrometer). How are the serial and model codes is yet to be defined,
        but we expect a maximum 50 character length code for serial and 30 for
        model.
        
        '''
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            str(self.info['id']) + '/command/GET_DEVICE_INFO'
        r = requests.get(cmd_url, cookies=self.info['cookiejar'], verify=False)   
        in4 = dict(r.json())['data'] 
        return in4
    
    def set_colour_priority(self, colour_priority):
        '''
        Command the luminaire to always first approximate to the desired color 
        of the spectrum to set before setting the spectrum channel values. 
        This function is set to true or false (enabled or disabled).

        Parameters
        ----------
        colour_priority : bool
            whether to enable or disable colour priority

        Returns
        -------
        None.

        '''
        data = {'arg' : colour_priority}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            str(self.info['id']) + '/command/SET_COLOR_PRIORITY'
        requests.post(cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)   

    def get_colour_priority(self):
        '''
        Get current color priority configuration for this luminaire.
        
        Returns
        -------
        colour_priority : bool
            Whether colour priority is enabled.
            
        '''
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            str(self.info['id']) + '/command/GET_COLOR_PRIORITY'
        r = requests.get(cmd_url, cookies=self.info['cookiejar'], verify=False)   
        colour_priority = dict(r.json())['data'] 
        return colour_priority
    
    def get_spectrometer_integration_time(self):
        '''
        Get the current integration time used by the spectrometer for gathering data.

        Returns
        -------
        integration_time : int
            A positive integer ranging from 50 to 140000 in tenths of millisecond.

        '''
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            str(self.info['id']) + '/command/GET_SPECTROMETER_INTEGRATION_TIME'
        r = requests.get(cmd_url, cookies=self.info['cookiejar'], verify=False)   
        integration_time = dict(r.json())['data'] 
        return integration_time
    
    def set_spectrometer_integration_time(self, integration_time):
        '''
        Sets the integration time of the spectrometer to gather data. Longer 
        times will result in more light reaching the sensor (like exposure 
        time in photography). Special attention should be taken to avoid 
        signal saturation.

        Parameters
        ----------
        integration_time : int
            A positive integer ranging from 50 to 140000 in tenths of millisecond.

        Returns
        -------
        None.

        '''
        data = {'arg' : integration_time}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            str(self.info['id']) + '/command/SET_SPECTROMETER_INTEGRATION_TIME'
        requests.post(cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)   
        
    def get_input_power(self):
        '''
        Returns the current consumed electrical power of the luminaire in mW.

        Returns
        -------
        input_power : int
            The electrical power at the luminaire in mW..

        '''
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            str(self.info['id']) + '/command/GET_INPUT_POWER'
        r = requests.get(cmd_url, cookies=self.info['cookiejar'], verify=False)   
        input_power = dict(r.json())['data'] 
        return input_power
    
    def set_dimming_level(self, dimming_level):
        '''
        Sets an intensity dimmer. This percentage modulates the current intensity 
        by multiplying the power count of each luminaire channel, i.e. if you 
        send a spectrum where each channel count is at half level and the dimming 
        is set at 50%, the final light intensity will be one quarter of the 
        luminaire full capacity.

        Parameters
        ----------
        dimming_level : int
            Percentage dimming level.

        Returns
        -------
        None.

        '''
        data = {'arg' : dimming_level}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            str(self.info['id']) + '/command/SET_DIMMING_LEVEL'
        requests.post(cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)   
    
    def get_dimming_level(self):
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            str(self.info['id']) + '/command/GET_DIMMING_LEVEL'
        r = requests.get(cmd_url, cookies=self.info['cookiejar'], verify=False)   
        dimming_level = dict(r.json())['data'] 
        return dimming_level
    
    # see RESTFUL_API for further mehods and define here if needed
    # def new_method_from_restful_api(self)...

    # User-defined functions 
    def full_readout(self, setting={}):
        '''
        Get a full readout from the STLAB.

        Parameters
        ----------
        setting : dict, optional
            The current setting of the luminaire (if known), to be included in
            the info_dict. For example {'led' : 5, 'intensity' : 3000}, or 
            {'intensities' : [0, 0, 0, 300, 4000, 200, 0, 0, 0, 0]}. 
            The default is {}.

        Returns
        -------
        counts : TYPE
            DESCRIPTION.
        info_dict : TYPE
            DESCRIPTION.

        '''
        tmps = self.get_pcb_temperature()
        ip   = self.get_input_power()
        it   = self.get_spectrometer_integration_time()
        dl   = self.get_dimming_level()
        rmv, counts = self.get_spectrometer_spectrum(norm=False)
        info_dict = {
            'rmv'              : rmv,
            'LEDs_temp'        : tmps[0],
            'drivers_temp'     : tmps[1],
            'board_temp'       : tmps[2],
            'micro_temp'       : tmps[3],
            'integration_time' : it,
            'input_power'      : ip,
            'dimming_level'    : dl
            }
        info_dict = {**info_dict, **setting}
        return counts, info_dict
    
    def sample(self, 
               leds=[0], 
               intensities=[500], 
               spectra=None,
               wait_before_sample=.2,
               ocean_optics=None,
               randomise=False,
               save_output=False):
        '''
        Sample a set of LEDs individually at a range of specified intensities 
        using the STLABs on-board spectrometer. Or, alternatively, sample a set
        of pre-defined spectra. Option to also obtain concurrent measurements 
        with an external Ocean Optics spectrometer.
    
        Parameters
        ----------
        leds : list, optional
            List of unique integers from 0-9 representing the LEDs to sample.
            The default is [0].
        intensities : list, optional
            List of integer values between 0-4095 representing the intensity 
            values at which to sample the LEDs. The default is [500].
        spectra : list, optinal
            List of predfined spectra to sample. Must be None if specifying
            leds or intensities. The default is None.
        wait_before_sample : float, optional
            Time in seconds to wait after setting a spectrum before acquiring 
            a measurement from the spectrometer(s). The default is .2.
        ocean_optics : seabreeze.spectrometers.Spectrometer, optional
            Whether to acquire concurrent measurements from an Ocean Optics 
            spectrometer. Requires the seabreeze package to be installed.
            The default is None.
        randomise : bool, optional
            Whether to randomise the order in which the LED-intensity settings 
            or spectra are sampled. The default is False.
        save_output : bool, optional
            Whether to save the samples and info as .csv files in the current
            working directory.
    
        Returns
        -------
        stlab_spectra : pd.DataFrame
            The resulting measurements from the STLAB spectrometer.
        stlab_info : pd.DataFrame
            The companion info to stlab_spectra, with matching indices.
        oo_spectra : pd.DataFrame, optional
            The resulting measurements from the Ocean Optics spectrometer.
        oo_info : pd.DataFrame, optional
            The companion info to the oo_spectra, with matching indices.
            
        '''
        if spectra and (leds or intensities):
            raise ValueError('leds and intensities must be None when specifying spectra')
  
        # off spectrum    
        leds_off = [0]*10
        
        # list to store stlab spectrometer data
        stlab_spectra = []
        stlab_info  = []
        
        # list to store ocean optics spectrometer data, if required
        if ocean_optics:
            oo_spectra = []
            oo_info  = []

        # turn stlab off if it's on
        self.set_spectrum_a(leds_off)
        
        # generate the settings
        if spectra:
            settings = spectra
            print('Sampling {} spectra: {}'.format(
                len(spectra), spectra))
        else:
            settings = [(l, i) for l in leds for i in intensities]
            print('Sampling {} leds at the following intensities: {}'.format(
                len(leds), intensities))
        
        # shuffle
        if randomise:
            shuffle(settings)
        
        # begin sampling            
        for i, s in enumerate(settings):
            if not spectra:
                led, intensity = s[0], s[1]
                setting = {'led' : led, 'intensity' : intensity}
                s = [0] * 10
                s[led] = intensity
                print('Measurement: {} / {}, LED: {}, intensity: {}'.format(
                    i + 1, len(settings), led, intensity))
            else:
                setting = {'intensities' : s}
                print('Measurement: {} / {}, spectrum: {}'.format(
                    i + 1, len(settings), s))
                       
            # set the spectrum
            self.set_spectrum_a(s)
            sleep(wait_before_sample)
            
            # full readout from STLAB
            stlab_counts, stlab_info_dict = self.full_readout(setting=setting)
            stlab_spectra.append(stlab_counts)
            stlab_info.append(stlab_info_dict)
            
            if ocean_optics:
                oo_counts, oo_info_dict = adaptive_measurement(
                    ocean_optics, setting=setting)
                oo_spectra.append(oo_counts)
                oo_info.append(oo_info_dict)
        
        # make dfs
        stlab_spectra = pd.DataFrame(stlab_spectra)
        stlab_spectra.columns = self.wlbins
        stlab_info = pd.DataFrame(stlab_info)
        
        if ocean_optics:
            oo_spectra = pd.DataFrame(oo_spectra)
            oo_spectra.columns = ocean_optics.wavelengths()
            oo_info = pd.DataFrame(oo_info)
            # TODO: check this works
            # oo_spectra[['led','intensity']] = oo_info[['led','intensity']]

        
        # turn off
        self.turn_off()
        
        if save_output:
            fid = datetime.now().strftime('%D-%H-%M').replace('/','-')
            stlab_spectra.to_csv('stlab_spectra_' + fid + '.csv')
            stlab_info.to_csv('stlab_info_' + fid + '.csv')
            if ocean_optics:
                oo_spectra.to_csv('oo_spectra_' + fid + '.csv')
                oo_info.to_csv('oo_info_' + fid + '.csv')
            
        if ocean_optics:
            return stlab_spectra, stlab_info, oo_spectra, oo_info
        else:
            return stlab_spectra, stlab_info

#################################
# FUNCTIONS TO MAKE VIDEO FILES #
#################################
def _get_header(df, repeats=1):
    return {
        'version':'1',
        'model':'VEGA10',
        'channels':10,
        'spectracount':len(df),
        'transitionsCount':len(df),
        'fluxReference':0,
        'repeats':repeats
        }

def _get_metadata(df, creator='jtm'):
    return {
        'creation_time':str(datetime.now()),
        'creator':creator
        }

def _get_spectra(df):
    light_cols = df.columns[1:]
    return df[light_cols].values.tolist()

def _get_transitions(df):
    list_of_dicts = []
    for index, row in df.iterrows():
        list_of_dicts.append({
            'spectrum':index,
            'power':100,
            'time':int(row['time']),
            'flags':0
            })
    return list_of_dicts

def get_time_vector(duration):
    t = np.arange(0, (duration * 1000), 10).astype("int")
    return t

def sinusoid_modulation(f, duration, Fs=100):
    x  = np.arange(duration * Fs)
    sm = np.sin(2 * np.pi * f * x / Fs)
    return sm

def modulate_intensity_amplitude(sm, background, amplitude):
    ivals = (background + (sm * amplitude)).astype("int")
    return ivals

def get_video_cols():
    cols = ['LED-' + str(val) for val in range(1, 11)]
    cols.insert(0, 'time')
    return cols

def make_video_file(df, video_nm='our_video_file', repeats=1):
    ''' 
    Takes a DataFrame with columns 'time', 'LED-1'...'LED-10'
    and save it as a .dsf ('dynamic sequence file') in the current
    working directory. The .dsf file can be loaded and played as a video stream
    with the STLAB.
    '''
    d = {
        'header':_get_header(df, repeats),
        'metadata':_get_metadata(df),
        'spectra':_get_spectra(df),
        'transitions':_get_transitions(df)
        }
    with open(video_nm + '.dsf', 'w') as outfile:
        json.dump(d, outfile)
    print('"{}" saved in the current working directory.'.format(video_nm + '.dsf'))

def _video_file_row(time=0, spec=[0,0,0,0,0,0,0,0,0,0]):
    fields = [time] + spec
    row = pd.DataFrame(fields).T
    cols = get_video_cols()
    row.columns = cols
    return row

def _video_file_end(end_time):
    df = pd.DataFrame()
    df = df.append(_video_file_row(time=end_time))     # two extra dummy rows ensure the light 
    df = df.append(_video_file_row(time=end_time + 100)) # turns off when video file finishes
    return df

def make_video_pulse(pulse_spec, 
                     pulse_duration, 
                     video_nm='our_video_file', 
                     return_df=False):
    '''
    Generate a video file to deliver a pulse of light.

    Parameters
    ----------
    pulse_spec : list
        Sprectrum to use for the pulse of light.
    pulse_duration : int
        Duration of the pulse.
    video_nm : str
        Name for the video file.
    return_df : bool
        Whether to return the DataFrame used to create the video file.
        
    Returns
    -------
    df : pd.DataFrame
        The DataFrame passed to make_video_file (if requested).

    '''
    df = pd.DataFrame()
    df = df.append(_video_file_row(0, pulse_spec))
    df = df.append(_video_file_row(pulse_duration, pulse_spec))
    df = df.append(_video_file_end(pulse_duration))     
    df.reset_index(inplace=True, drop=True)
    make_video_file(df, video_nm)
    if return_df:
        return df
    
def make_video_pulse_background(background_spec, 
                                pre_background_duration,
                                pulse_spec, 
                                pulse_duration, 
                                post_background_duration, 
                                video_nm='our_video_file', 
                                return_df=False):
    '''
    Generate a video file to deliver a pulse of light against a background
    of light. Clunky but works well.

    Parameters
    ----------
    background_spec : list
        The background spectrum.
    pre_background_duration : int
        Duration of the background prior to pulse.
    pulse_spec : list
        The pulse spectrum..
    pulse_duration : int
        Duration of the pulse.
    post_background_duration : int
        Duration of the background after the pulse..
    return_df : bool, optional
        Whether to return the DataFrame. The default is False.
    video_nm : str, optional
        Name for the video file. The default is 'our_video_file'.

    Returns
    -------
    df : pd.DataFrame
        The DataFrame passed to make_video_file (if requested).

    '''
    
    df = pd.DataFrame()
    onset  = pre_background_duration
    offset = onset+pulse_duration
    end    = offset+post_background_duration
    df = df.append(_video_file_row(0, background_spec))
    df = df.append(_video_file_row(pre_background_duration, background_spec))
    df = df.append(_video_file_row(pre_background_duration, pulse_spec))
    df = df.append(_video_file_row(pre_background_duration + pulse_duration, pulse_spec))
    df = df.append(_video_file_row(pre_background_duration + pulse_duration, background_spec))
    df = df.append(_video_file_row(end, background_spec))
    df = df.append(_video_file_end(end))
    df.reset_index(inplace=True, drop=True)
    make_video_file(df, video_nm)
    if return_df:
        return df
            

# def make_video_baden_chirp(led, 
#                            mintensity=0, 
#                            maxtensity=4095, 
#                            Fs=100, 
#                            videoname='chripstim',
#                            pulse_duration=1,
#                            post_pulse_wait=7,
#                            phase1_params=(0.01, 1, 20),
#                            phase2_params=(1, 20),
                           
#                            ):
    
    
    
    
def video_file_to_dict(video_file):
    '''
    Unpack a video file into a dictionary with keys ['header', 'metadata', 
    'spectra', 'transitions'] 

    Parameters
    ----------
    video_file : str
        The video file to unpack.

    Returns
    -------
    data : dict
        the video file as a dictionary.

    '''
    with open(video_file) as vf:
        data = json.load(vf)
    return data

###################################################
# ADDITIONAL FUNCTIONS FOR WORKING WITH THE STLAB #
###################################################
    
def plot_spectrum(spectrum, color):
    bins = np.linspace(380,780,81)
    plt.plot(bins, spectrum, color=color)

def interp_spectra(spectra):
    '''
    This function needs generalising.

    Parameters
    ----------
    spectra : TYPE
        DESCRIPTION.

    Returns
    -------
    intp_tbl : TYPE
        DESCRIPTION.

    '''
    tbl = spectra.unstack(level=2)
    tbl.columns = [val[1] for val in tbl.columns]
    
    intp_tbl = pd.DataFrame()
    for led, df in tbl.groupby(['led']):
        intensities = df.index.get_level_values('intensity')
        new_intensities = np.linspace(intensities.min(), intensities.max(), 4096)
        new_intensities = new_intensities.astype('int')
        df.reset_index(inplace=True, drop=True)
        df.columns = range(0, df.shape[1])
        df.index = df.index * 63
        n = df.reindex(new_intensities).interpolate(method='linear')
        n['intensity'] = n.index
        n['led'] = led
        intp_tbl = intp_tbl.append(n)
    intp_tbl.set_index(['led','intensity'], inplace=True)
    return intp_tbl

def predict_spd(intensity=[0,0,0,0,0,0,0,0,0,0], lkp_table=None):
    '''
    Predict the spectral power distribution for a given list of led 
    intensities using linear interpolation.

    Parameters
    ----------
    intensity : list
        List of intensity values for each led. The default is [0,0,0,0,0,0,0,0,0,0].
    lkp_table : DataFrame
        A wide-format DataFrame with hierarchichal pd.MultIndex [led, intensity] 
        and a column for each of 81 5-nm wavelength bins. 4096*10 rows, containing
        predicted output for each led at all possible intensities.

    Returns
    -------
    spectrum : np.array
        Predicted spectrum for given intensities.
        
    '''
    spectrum = np.zeros(81)
    for led , val in enumerate(intensity):
        spectrum += lkp_table.loc[(led,val)].to_numpy()
    return spectrum

def get_led_colors():
    colors = ['blueviolet', 'royalblue', 'darkblue',
              'blue', 'cyan', 'green', 'lime',
              'orange','red','darkred']
    return colors

def get_wlbins(bin_width=5):
    if bin_width==1:
        wlbins = [int(val) for val in np.linspace(380, 780, 81 * bin_width)]
    else:
        wlbins = [int(val) for val in np.linspace(380, 780, 81)]
    return wlbins

def spec_to_xyz(spec):
    '''
    Convert a spectrum to an xyz point.

    The spectrum must be on the same grid of points as the colour-matching
    function, cmf: 380-780 nm in 5 nm steps.

    '''
    from CIE import get_CIE_CMF
    
    cmf = get_CIE_CMF()[1:]
    cmf = cmf.T
    XYZ = np.sum(spec[:, np.newaxis] * cmf, axis=0)
    den = np.sum(XYZ)
    if den == 0.:
        return XYZ
    return XYZ / den

def spectra_to_xyz(spectra):
    '''
    Calculate the CIE 1931 xy chromaticity coordinates for a collection of
    spectra. The DataFrame must have columns (or multi index) with names

    Parameters
    ----------
    spectra : DataFrame
        As output by stlab.sample_leds

    Returns
    -------
    xyz : DataFrame
        The xyz values for each spectrum.
        
    '''
    idx = []    
    xyz = []
    for i, spec in spectra.groupby(by=['led','intensity']):
        idx.append(i)
        xyz.append(spec_to_xyz(spec['flux'].to_numpy()))
    xyz = pd.DataFrame(xyz, columns=['X','Y','Z'])
    xyz.index = pd.MultiIndex.from_tuples(idx, names=['led','intensity'])
    return xyz

def spectra_to_peak_wavelengths(spectra):
    '''
    Calculate the peak wavelengths for a given set of spectra.

    Parameters
    ----------
    spectra : TYPE
        DESCRIPTION.

    Returns
    -------
    pwl : TYPE
        DESCRIPTION.

    '''
    idx = []    
    pwl = []
    for i, spec in spectra.groupby(by=['led','intensity']):
        idx.append(i)
        pwl.append(spec.loc[spec['flux']==spec['flux'].max(), 'wavelength'].to_numpy()) 
    pwl = pd.DataFrame(pwl, columns=['wavelength'])
    pwl.index = pd.MultiIndex.from_tuples(idx, names=['led','intensity'])
    return pwl

def spectra_to_dominant_wavelength(spectra, ref_white=[0.3333, 0.3333]):
    from colour.colorimetry.dominant import dominant_wavelength
    
    xyz = spectra_to_xyz(spectra)
    idx = []
    dwl = []
    for i, row in xyz.iterrows():
        result = dominant_wavelength((row.X, row.Y), ref_white)
        dwl.append(result[0])
        idx.append(i)
    dwl = pd.DataFrame(dwl, columns=['wavelength'])
    dwl.index = pd.MultiIndex.from_tuples(idx, names=['led','intensity'])
    return dwl

def spectra_to_melanopic_irradiance(spectra, grouper=['led','intensity']):
    from CIE import get_CIES026
    
    # get melanopsin sensitivity
    _ , sss = get_CIES026(asdf=True)
    mel = sss['Mel']
    mel = mel[::5]
    
    # aggregate to melanopic irradiance
    mi = spectra.groupby(by=grouper)['flux'].agg(lambda x: x.dot(mel.values.T))
    return mi

def spectra_to_luminance(spectra, grouper=['led','intensity']):
    from CIE import get_CIE_1924_photopic_vl
    
    # get luminancephotopic luminance curve
    vl = get_CIE_1924_photopic_vl(asdf=True)
    vl = vl[::5]
    
    # aggregate to luminance
    lum = spectra.groupby(by=grouper)['flux'].agg(lambda x: x.dot(vl.values))
    return lum    

 
def explore_spectra(spectra):
    '''
    This function takes a DataFrame of spectra and plots them, along with other
    useful info.
    '''
    from colour.plotting import plot_chromaticity_diagram_CIE1931
    import seaborn as sns
    
    # get xy chromaticities
    xyz = spectra_to_xyz(spectra)
    
    # get peak wavelength
    pwl = spectra_to_peak_wavelengths(spectra)
    
    # get dominant wavelength
    dwl = spectra_to_dominant_wavelength(spectra)
    
    # get malanopic irradiances
    mi = spectra_to_melanopic_irradiance(spectra)

    # set up figure
    fig , ax = plt.subplots(10, 4, figsize=(16,36))
    colors = get_led_colors()

    for i, led in enumerate(ax):
    
        # plot spectra
        sns.lineplot(x='wavelength', y='flux', data=spectra[spectra.led==i], color=colors[i], units='intensity',ax=ax[i, 0], lw=.1, estimator=None)
        ax[i, 0].set_ylim((0,3500))
        ax[i, 0].set_xlabel('Wavelength $\lambda$ (nm)')
        ax[i, 0].set_ylabel('Flux (mW)')
    
        # plot color coordinates
        plot_chromaticity_diagram_CIE1931(standalone=False, axes=ax[i, 1], title=False, show_spectral_locus=False)
        ax[i, 1].set_xlim((-.15,.9))
        ax[i, 1].set_ylim((-.1,1))
        ax[i, 1].scatter(xyz.loc[i,'X'], xyz.loc[i,'Y'], c='k', s=3)
        
        # plot peak and dominant wavelength as a function of input
        inpt = spectra['intensity'] / 4095
        inpt = np.linspace(0, 1, len(spectra.intensity.unique()))
        ax[i, 2].plot(inpt, pwl.loc[i, 'wavelength'], color=colors[i], lw=1, label='Peak')
        ax[i, 2].set_xlabel('Input')
        
        ax[i, 2].plot(inpt, dwl.loc[i, 'wavelength'], color=colors[i], lw=3, label='Dominant')
        ax[i, 2].set_xlabel('Input')
        ax[i, 2].set_ylabel('$\lambda$ (nm)')
        low  = dwl.loc[i, 'wavelength'].min()-dwl.loc[i, 'wavelength'].min()*0.1
        high = dwl.loc[i, 'wavelength'].max()+dwl.loc[i, 'wavelength'].max()*0.1
        ax[i, 2].set_ylim((low, high))
        ax[i, 2].legend()
        
        # plot melanopic irradience
        ax[i, 3].plot(inpt, mi.loc[i], color=colors[i])
        ax[i, 3].set_ylim((0,14000))
        ax[i, 3].set_xlabel('Input')
        ax[i, 3].set_ylabel('Melanopic irradiance (mW)')
    
    return fig    

# pulse_spec=[300,300,300,300,300,3000,3000,3000,300,300]
# pulse_duration =1000
# background_spec = [300,300,300,300,300,300,300,300,300,300]
# pre_background_duration=3000
# post_background_duration=3000
# df = make_video_pulse_background(pulse_spec=pulse_spec, pulse_duration=pulse_duration,
#                       return_df=True,
#                       pre_background_duration=pre_background_duration,
#                       post_background_duration=post_background_duration, background_spec=background_spec)

def led_radiance_match(led, intensity, match_led, lkp_tbl):
    radiance_lkp = lkp_tbl.sum(axis=1)
    led_radiance = radiance_lkp.loc[(led, intensity)]
    match_intensity = radiance_lkp.loc[match_led].sub(led_radiance).abs().idxmin()
    error = radiance_lkp.loc[match_led].sub(led_radiance).abs().min()
    return error, match_intensity
