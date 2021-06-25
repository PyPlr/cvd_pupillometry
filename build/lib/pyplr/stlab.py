#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
pyplr.stlab
===========

A python wrapper for Ledmotive's Spectra Tune Lab light engine and RESTful API.
See the "LIGHT HUB RESTful API" manual for further functions and more info. 
Note that a license is required to develop against the RESTful API.

'''

from time import sleep
from datetime import datetime
import json

import requests
import numpy as np
import pandas as pd

class SpectraTuneLab:
    '''Wrapper for LEDMOTIVE Spectra Tune Lab RESTFUL_API. 
        
    Attributes
    ----------
    colors : string
        Matplotlib colornames for the 10 channels.
    rgb_colors : list
        RGB colors of the 10 channels taken from photographs.
    wlbins : list
        The wavelength bins for the on-board spectrometer.
    min_intensity : int
        The minimum intensity setting for LEDs.
    max_intensity : int
        The maximum intensity setting for the LEDs.
        
    Examples
    --------
    >>> # Synchronous mode
    >>> # Set each LED to maximum for a few seconds
    >>> d = SpectraTuneLab(username='admin', identitiy=1, password='*')
    >>> for led in range(10):
    ...     spectrum = [0]*10
    ...     spectrum[led] = 4095
    ...     d.set_spectrum_a(spectrum)
    ...     sleep(2.)
    >>> d.turn_off()
    
    >>> # Asynchronous mode
    >>> # create and play a video file setting all LEDs to maximum for 1 second
    >>> pulse_protocol(pulse_spec=[4095]*10,
    ...                pulse_duration=1000,
    ...                video_name='my_video_file')
    >>> d = SpectraTuneLab(username='admin', identitiy=1, password='*')
    >>> d.load_video_file('my_video_file')
    >>> d.play_video_file()
        
    '''
    # Class attributes
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
    def __init__(self, password, username='admin', identity=1, 
                 lighthub_ip='192.168.7.2'):
        '''Initialize connection with LightHub. 
        
        Parameters
        ----------
        username : string
            The username for logging in. 
        identity : int
            A unique numerical identifier for the device. 
        password : string
            The password specific to the LightHub.
        lightub_ip : string, optional
            The IP address of the LightHub device. The default is 
            `'192.168.7.2'`.
            
        Note
        ----
        The Mac connection driver usually creates the network in a way that
        places the LightHub device at IP 192.168.6.2 instead of IP 192.168.7.2,
        so this may need to be changed depending on the platform. If that is 
        not enough, you might need to also install the two (                
        `Network <https://beagleboard.org/static/Drivers/MacOSX/RNDIS/HoRNDIS.pkg>`_
        and
        `Serial <https://beagleboard.org/static/Drivers/MacOSX/FTDI/EnergiaFTDIDrivers2.2.18.pkg>`_
        ) Mac OX drivers required by the BeagleBone (the LightHub motherboard).

        Returns
        -------
        None.

        '''
        self.username = username
        self.id = str(identity)
        self.password = password
        self.lighthub_ip = lighthub_ip
        self.info = {}

        try:
            cmd_url = 'http://' + self.lighthub_ip + ':8181/api/login'
            a = requests.post(cmd_url, 
                              json={'username': username,
                                    'password': password}, 
                              verify=False)
            cookiejar = a.cookies
            sleep(.1)
            self.info = {
                'url': self.lighthub_ip,
                'id': identity,
                'cookiejar': cookiejar}
            
            more_info = self.get_device_info()
            self.info = {**self.info, **more_info}
            # for some reason, after first turning on the STLAB, video files 
            # won't play unless you first do something in synchronous mode. A 
            # quick call to spectruma at startup gets around this issue, but 
            # it might be a good idea to ask Ledmotive about this. Also, the
            # first time you do play a video file, it often flickers.
            # USE MULTICAST ADDRESS!
            self.spectruma([0,0,0,0,0,0,0,0,1,1]) 
            sleep(.2)
            self.turn_off()
            print('STLAB device setup complete...')
            
        except requests.RequestException as err:
            print('login error: ', err)
        
    # Functions wrapped from STLAB's RESTFUL_API (incuding relevant documentation)
    def set_spectrum_a(self, intensity_values):
        '''Executes a spectrum based on the intensity values provided for each 
        of the channels. Each channel can be set between 0 and 4095 (only integer 
        values).
    
        Parameters
        ----------
        intensity_values : list
            List of 10 integer values between 0 and 4095.
    
        Returns
        -------
        None.
            None.
        
        '''
        data = {'arg': intensity_values}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            self.id + '/command/SET_SPECTRUM_A'
        requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)
    
    def set_spectrum_s(self, spectrum):
        '''Executes the given spectrum. The spectrum is defined by an array of 
        81 elements that represents 5 nm wavelength bins from 380 nm to 780 nm.
        The values are an abstraction of the light intensity at each point 
        that allows the reconstruction of the spectrum shape. Each value ranges 
        between 0 and 65535, 0 being no intensity and 65535 being full intensity 
        at the corresponding wavelength bin (prior application of dimming and 
        power protection caps).

        Parameters
        ----------
        spectrum : list
            List of 81 (the 380 nm to 780 nm bins) integer values between 
            0 and 65535.

        Returns
        -------
        None.
            None.

        '''
        data = {'arg': spectrum}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            self.id + '/command/SET_SPECTRUM_S'
        requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)
        
    def spectruma(self, intensity_values):
        '''Executes a spectrum based on the intensity values provided for each 
        of the channels. Each channel can be set between 0 and 4095. This is an 
        alternative way to the command `set_spectrum_a` that allows setting a 
        spectrum issuing a `GET` command (which allows access to the luminaire 
        by typing a url in any browser). 
        
        Parameters
        ----------
        intensity_values : list
            List of 10 integer values between 0 and 4095.
    
        Returns
        -------
        None.
            None.
        
        '''
        spec = ''.join([str(val) + ',' for val in intensity_values])[:-1]
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            self.id + '/spectruma/' + spec
        requests.get(cmd_url, cookies=self.info['cookiejar'], verify=False)
    
    def color_xy(self, intensity_values, x, y):
        '''Similar to the `spectruma` command, but allows setting a target 
        `x, y` coordinates in the CIE1931 color space. 
    
        Parameters
        ----------
        intensity_values : list
            The desired spectrum as a list of integers.
        x : float
            Desired target CIE1931 `x` coordinate as a decimal number.
        y : float
            Desired target CIE1931 `y` coordinate as a decimal number.
    
        Returns
        -------
        None.
            None.
        
        '''
        spec = ''.join([str(val) + ',' for val in intensity_values])[:-1]
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            self.id + '/spectruma/' + spec + '/color/' + \
                str(x) + '/' + str(y)
        requests.get(cmd_url, cookies=self.info['cookiejar'], verify=False)

    def set_color(self, x, y, flux=None):
        '''Executes a light color represented in the CIE1931 color space. The
        `x` and `y` coordinates are the mathematical index that represents the
        target color to be achieved. If the `x,y` provided values are not 
        available by the system, it will find its nearest available x,y 
        coordinates. If flux is provided as an argument, it will be adjusted 
        automatically, otherwise the current flux will be used. 
    
        Parameters
        ----------
        x : float
            Desired target CIE1931 `x` coordinate as a decimal number.
        y : float
            Desired target CIE1931 `y` coordinate as a decimal number.
        flux : int, optional
            Value between 0 and 4095. The default is None.
    
        Returns
        -------
        None.
            None.
        
        '''
        if flux:
            data = {'arg': [x, y, flux]}
        else:
            data = {'arg': [x, y]}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            self.id + '/command/SET_COLOR'
        requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)
    
    def turn_off(self):
        '''Stops light emission by setting the power at all channels to 0.   
        
        Parameters
        ----------
        None.
    
        Returns
        -------
        None.
            None.
        
        '''
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            self.id + '/command/TURN_OFF'
        requests.post(cmd_url, cookies=self.info['cookiejar'], verify=False) 
    
    def set_blink(self, blink=1):
        '''Commands the luminaire to blink. The value provided as an argument 
        is the number of times the light blinks in one second.
    
        Parameters
        ----------
        blink : int, optional
            Number of times the light should blink in one second. The default
            is 1.
    
        Returns
        -------
        None.
            None.
        
        '''
        data = {'arg': blink}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            self.id + '/command/SET_BLINK'
        requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False) 
  
    def get_pcb_temperature(self):
        '''Returns the PCB temperature in Celsius degrees (ºC). Returns a list 
        of 4 elements in this order: LEDs, Drivers, Spectrometer and 
        Microcontroller temperature sensors close to these elements. If one 
        sensor or its readout is not available a null value is returned for
        that element. 
        
        Parameters
        ----------
        None.
    
        Returns
        -------
        temperatures : np.array
            [Number, Number, Number, Number].
            
        '''
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            self.id + '/command/GET_PCB_TEMPERATURE'
        r = requests.get(cmd_url, cookies=self.info['cookiejar'], verify=False)
        temperatures = dict(r.json())['data']
        return temperatures
    
    def get_spectrum_a(self):
        '''Returns the current amplitude for each of the luminaire channels. 
        The array returned has a length equal to the channel count of the 
        luminaire. Each value in the array is a representation of electrical 
        counts, ranging from 0 to 4095 counts.

        Returns
        -------
        None.
            None.

        '''
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            self.id + '/command/GET_SPECTRUM_A'
        r = requests.get(cmd_url, cookies=self.info['cookiejar'], verify=False) 
        return np.array(dict(r.json())['data'][1:])
     
    def get_spectrometer_spectrum(self, norm=False):
        '''Returns the spectrum readout from the internal spectrometer. If the
        luminaire does only contain a colorimeter sensor, a theoretical 
        spectrum based on the current channel's power is obtained instead. The 
        data is returned in 81 elements that represents a 5 nm wavelength bins 
        from 380 nm to 780 nm. Each element is a value ranging from 0 to 65535
        abstracting the light intensity at each point and allowing the
        reconstruction of the spectral shape. An additional element represents 
        the radiometric value in milliWatts (mW) at the peak of a max value of
        a spectrum at which the abstracted values are normalized, i.e. the 
        flux corresponding to a 65535 value in the array. This flux depends on 
        multiple factors, as current channels power, dimming level, power 
        protection and maximum power of the lighted LEDs.     
    
        Parameters
        ----------
        norm : bool, optional
            Whether to normalize the spectrum to its peak radiometric value
    
        Returns
        -------
        spectrum : list
            [Number, Number, ..., Number, Number] with 81 elements.
            
        '''
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            self.id + '/command/GET_SPECTROMETER_SPECTRUM'
        r = requests.get(cmd_url, cookies=self.info['cookiejar'], verify=False) 
        rmv = dict(r.json())['data'][0]
        spectrum = np.array(dict(r.json())['data'][1:])
        if norm:
            return rmv, spectrum
        else:
            return rmv, spectrum * rmv
    
    def get_led_calibration(self):
        '''Returns the current LED calibration matrix containing 10 rows 
        (for each channel) and 81 columns (intensity value from 380 to 780 nm 
        in steps of 5 nm).     
        
        Returns
        -------
        matrix : list
            10 x 81 calibration matrix.
            
        '''
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            self.id + '/command/GET_LED_CALIBRATION'
        r = requests.get(cmd_url, cookies=self.info['cookiejar'], verify=False)   
        return dict(r.json())['data'] 
        
    def load_video_file(self, fname, return_vf_dict=True):
        '''Uploads a video light sequence file to the LIGHT HUB. The video
        file must follow the LEDMOTIVE Dynamic Sequence File (.dsf) format. 
        The uploaded file must be a json file (.dsf files are json files), 
        with weight less than 2 MB. The file must be uploaded using the 
        multipart / form-data standard convention. See ``play_video_file(...)``
        for how to play the uploaded file in a luminaire.  
    
        Parameters
        ----------
        video : string
            Name of the video file.
    
        Returns
        -------
        dict
            Video file dictionary if `return_vf_dict` is True else None.
        
        '''
        args = [('file', (fname, open(fname, 'rb'), 'application/json'))]
        cmd_url = 'http://' + self.info['url'] + ':8181/api/gateway/video' 
        r = requests.post(
            cmd_url, files=args, cookies=self.info['cookiejar'], verify=False)
        if 'data' not in r.json():
            raise 'Upload file error'
        print('video file loaded...')
        if return_vf_dict:
            return video_file_to_dict(fname)
        
    def play_video_file(self, broadcast=True, stop=False):
        '''Starts the execution of a light video sequence in the specified 
        luminaire or multicast address. If no video is in the LIGHT HUB, an 
        error response is raised, and the command ignored. If the video is 
        already playing, the play is interrupted, and the video is reproduced 
        back from the beginning. To stop the video, use `stop=True`. See 
        `load_video_file(...)` for how to load a video file. 
    
        Parameters
        ----------
        broadcast : bool
            Whether to issue the commmand via the broadcast address 1023. This
            avoids a bug at startup. The default is True.
        stop : bool, optional
            Whether the command should stop the video. The default is False.
    
        Returns
        -------
        None.
            None.

        '''
        address = '1023' if broadcast else self.id
        if stop:
            data = {'arg': None}
        else:
            data = {'arg': './data/video1.json'}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/PLAY_VIDEO_FILE'
        print('playing video file...')
        return requests.post(
            cmd_url, json=data, cookies=self.info['cookiejar'], verify=False)
        
    def get_device_info(self):
        '''Returns the device characteristics and basic configuration. These 
        are the serial code, the model code, the number of channels for this 
        luminaire and the device feedback type (whether it is colorimeter or 
        spectrometer). How are the serial and model codes is yet to be defined,
        but expect a maximum 50 character length code for serial and 30 for
        model.
        
        Returns
        -------
        dict
            The device info.
        
        '''
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            self.id + '/command/GET_DEVICE_INFO'
        r = requests.get(cmd_url, cookies=self.info['cookiejar'], verify=False)   
        return dict(r.json())['data'] 
    
    def set_colour_priority(self, colour_priority):
        '''Command the luminaire to always first approximate to the desired 
        color of the spectrum to set before setting the spectrum channel 
        values. This function is set to true or false (enabled or disabled).

        Parameters
        ----------
        colour_priority : bool
            Whether to enable or disable colour priority.

        Returns
        -------
        None.
            None.

        '''
        data = {'arg': colour_priority}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            self.id + '/command/SET_COLOR_PRIORITY'
        requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)   

    def get_colour_priority(self):
        '''Get current color priority configuration for this luminaire.
        
        Returns
        -------
        colour_priority : bool
            Whether colour priority is enabled.
            
        '''
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            self.id + '/command/GET_COLOR_PRIORITY'
        r = requests.get(cmd_url, cookies=self.info['cookiejar'], verify=False)   
        return dict(r.json())['data'] 
    
    def get_spectrometer_integration_time(self):
        '''Get the current integration time used by the spectrometer for
        gathering data.

        Returns
        -------
        integration_time : int
            A positive integer ranging from 50 to 140000 in tenths of 
            millisecond.

        '''
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            self.id + '/command/GET_SPECTROMETER_INTEGRATION_TIME'
        r = requests.get(cmd_url, cookies=self.info['cookiejar'], verify=False)   
        return dict(r.json())['data'] 
    
    def set_spectrometer_integration_time(self, integration_time):
        '''Sets the integration time of the spectrometer to gather data. Longer 
        times will result in more light reaching the sensor (like exposure 
        time in photography). Special attention should be taken to avoid 
        signal saturation.

        Parameters
        ----------
        integration_time : int
            A positive integer ranging from 50 to 140000 in tenths of
            millisecond.

        Returns
        -------
        None.
            None.

        '''
        data = {'arg': integration_time}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            self.id + '/command/SET_SPECTROMETER_INTEGRATION_TIME'
        requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)   
        
    def get_input_power(self):
        '''Returns the current consumed electrical power of the luminaire in
        mW.

        Returns
        -------
        input_power : int
            The electrical power at the luminaire in mW.

        '''
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            self.id + '/command/GET_INPUT_POWER'
        r = requests.get(cmd_url, cookies=self.info['cookiejar'], verify=False)   
        return dict(r.json())['data'] 
    
    def set_dimming_level(self, dimming_level):
        '''Sets an intensity dimmer. This percentage modulates the current 
        intensity by multiplying the power count of each luminaire channel,
        i.e. if you send a spectrum where each channel count is at half level
        and the dimming is set at 50%, the final light intensity will be one 
        quarter of the luminaire full capacity.

        Parameters
        ----------
        dimming_level : int
            Percentage dimming level.

        Returns
        -------
        None.
            None.

        '''
        data = {'arg': dimming_level}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            self.id + '/command/SET_DIMMING_LEVEL'
        requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)   
    
    def get_dimming_level(self):
        '''Returns the user intensity dimmer. See `set_dimming_level(...)` for
        more info.
        
        Returns
        -------
        None.
            None.

        '''
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            self.id + '/command/GET_DIMMING_LEVEL'
        r = requests.get(cmd_url, cookies=self.info['cookiejar'], verify=False)   
        return dict(r.json())['data'] 
    
    def set_multicast_address(self, address=[1001, None, None, None]):
        '''Sets an array of multicast addresses accepted by the luminaire. A 
        multicast address can be shared by different luminaires. Thus, when
        using a multicast address as the luminaire id of one request, the 
        appropriate command is issued to all the luminaires sharing the same
        multicast address. Currently only the response of the first luminaire 
        to answer is returned to the caller client. Currently 4 multicast 
        addresses can be set in a single luminaire (which effectively limits
        the number of groups a luminaire can be part of to 4, without counting 
        the broadcast group). Each address should be in the range 1 - 1022 and
        should not be already in use by any luminaire id. The multicast address
        1023 is shared by all luminaires without the need to include it in this
        list, and can be used as a broadcast address to request commands in all
        the installation.

        Parameters
        ----------
        address : TYPE, optional
            DESCRIPTION. The default is [15,None,None,None].

        Returns
        -------
        None.

        '''
        data = {'arg': address}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            self.id + '/command/SET_MULTICAST_ADDRESS'
        requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)   
    
    def get_multicast_address(self):
        '''Returns the array of multicast addresses set in the luminaire. See 
        `.set_multicast_address(...)` for more info.
        
        Returns
        -------
        None.
            None.

        '''
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            self.id + '/command/GET_MULTICAST_ADDRESS'
        r = requests.get(cmd_url, cookies=self.info['cookiejar'], verify=False)   
        return dict(r.json())['data'] 
    
#################################
# FUNCTIONS TO MAKE VIDEO FILES #
#################################
def _get_header(df, repeats=1):
    return {
        'version': 1,
        'model': 'VEGA10',
        'channels': 10,
        'spectracount': len(df),
        'transitionsCount': len(df),
        'fluxReference': 0,
        'repeats': repeats
        }

def _get_metadata(df, creator='jtm', **metadata):
    default = {
        'creation_time': str(datetime.now()),
        'creator': creator
        }
    return {**default, **metadata}


def _get_spectra(df):
    light_cols = df.columns[1:]
    return df[light_cols].values.tolist()

def _get_transitions(df):
    list_of_dicts = []
    for index, row in df.iterrows():
        list_of_dicts.append({
            'spectrum': index,
            'power': 100,
            'time': int(row['time']),
            'flags': 0
            })
    return list_of_dicts

def get_time_vector(duration):
    t = np.arange(0, (duration*1000), 10).astype("int")
    return t

def sinusoid_modulation(f, duration, Fs=100):
    x  = np.arange(duration*Fs)
    sm = np.sin(2 * np.pi * f * x / Fs)
    return sm

def modulate_intensity_amplitude(sm, background, amplitude):
    ivals = (background + (sm*amplitude)).astype("int")
    return ivals

def get_video_cols():
    cols = ['LED-' + str(val) for val in range(1, 11)]
    cols.insert(0, 'time')
    return cols

def _video_file_row(time=0, spec=[0,0,0,0,0,0,0,0,0,0]):
    fields = [time] + spec
    row = pd.DataFrame(fields).T
    cols = get_video_cols()
    row.columns = cols
    return row

def _video_file_end(end_time):
    df = pd.DataFrame()
    df = (df.append(_video_file_row(time=end_time))      # two extra dummy rows ensure the light 
            .append(_video_file_row(time=end_time+100))) # turns off when video file finishes
    return df

def make_video_file(df, fname='our_video_file', repeats=1, **metadata):
    ''' 
    Takes a DataFrame with columns 'time', 'LED-1'...'LED-10'
    and save it as a .dsf ('dynamic sequence file') in the current
    working directory. The .dsf file can be loaded and played as a video stream
    with the STLAB.
    '''
    d = {
        'header': _get_header(df, repeats),
        'metadata': _get_metadata(df, **metadata),
        'spectra': _get_spectra(df),
        'transitions': _get_transitions(df)
        }
    with open(fname + '.dsf', 'w') as outfile:
        json.dump(d, outfile)
    print(
        '"{}" saved in the current working directory.'.format(fname + '.dsf'))
    
def pulse_protocol(pulse_spec, 
                   pulse_duration, 
                   fname='our_video_file', 
                   return_df=False,
                   metadata={}):
    '''
    Generate a video file to deliver a pulse of light.

    Parameters
    ----------
    spec : list
        Sprectrum to use for the pulse of light.
    duration : int
        Duration of the pulse in ms.
    video_name : str
        Name for the video file.
    return_df : bool
        Whether to return the DataFrame used to create the video file.
    metadata : dict
        Additional info to include in the metadata of the video file (e.g. 
        'color' : 'blue').
        
    Returns
    -------
    df : pd.DataFrame
        The DataFrame passed to make_video_file (if requested).

    '''
    metadata['protocol'] = 'pulse'
    metadata['pulse_spec'] = str(pulse_spec)
    metadata['pulse_duration'] = str(pulse_duration)
    df = pd.DataFrame()
    df = (df.append(_video_file_row(0, pulse_spec))
            .append(_video_file_row(pulse_duration, pulse_spec))
            .append(_video_file_end(pulse_duration))
            .reset_index(drop=True))
    make_video_file(df, fname, **metadata)
    if return_df:
        return df
    
def background_pulse_protocol(background_spec, 
                              pre_pulse_duration,
                              pulse_spec, 
                              pulse_duration, 
                              post_pulse_duration, 
                              fname='our_video_file', 
                              return_df=False,
                              metadata={}):
    '''
    Generate a video file to deliver a pulse of light (or dark) against a 
    background of light (or dark). Clunky but works well.

    Parameters
    ----------
    background_spec : list
        The background spectrum.
    pre_pulse_duration : int
        Duration of the background prior to pulse.
    pulse_spec : list
        The pulse spectrum..
    pulse_duration : int
        Duration of the pulse in ms.
    post_pulse_duration : int
        Duration of the background after the pulse..
    fname : str, optional
        Name for the video file. The default is 'our_video_file'.
    return_df : bool, optional
        Whether to return the DataFrame. The default is False.
    metadata : dict
        Additional info to include in the metadata field of the video file 
        (e.g. {'color' : 'blue'}). This info can be extracted when loading the 
        file during an experiment and included in triggers sent to Pupil 
        Capture. The default is {}.
        
    Returns
    -------
    df : pd.DataFrame
        The DataFrame passed to make_video_file (if requested).

    '''
    metadata['protocol'] = 'background_pulse'
    metadata['background_spec'] = int(background_spec)
    metadata['pre_pulse_duration'] = int(pre_pulse_duration)
    metadata['pulse_spec'] = int(pulse_spec)
    metadata['pulse_duration'] = int(pulse_duration)
    metadata['post_pulse_duration'] = int(post_pulse_duration)
    onset  = pre_pulse_duration
    offset = onset+pulse_duration
    end = offset+post_pulse_duration
    df = pd.DataFrame()
    df = (df.append(_video_file_row(0, background_spec))
            .append(_video_file_row(pre_pulse_duration, background_spec))
            .append(_video_file_row(pre_pulse_duration, pulse_spec))
            .append(_video_file_row(
                pre_pulse_duration+pulse_duration, pulse_spec))
            .append(_video_file_row(
                pre_pulse_duration+pulse_duration, background_spec))
            .append(_video_file_row(end, background_spec))
            .append(_video_file_end(end))
            .reset_index(drop=True))
    make_video_file(df, fname, **metadata)
    if return_df:
        return df
    
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

def get_led_colors(rgb=False):
    if rgb:
        colors = [[.220, .004, .773, 1.], [.095, .232, .808, 1.],
                  [.098, .241, .822, 1.], [.114, .401, .755, 1.],
                  [.194, .792, .639, 1.], [.215, .895, .489, 1.],
                  [.599, .790, .125, 1.], [.980, .580, .005, 1.],
                  [.975, .181, .174, 1.], [.692, .117, .092, 1.]]
    else:
        colors = ['blueviolet', 'royalblue', 'darkblue',
              'blue', 'cyan', 'green', 'lime',
              'orange','red','darkred']
    return colors