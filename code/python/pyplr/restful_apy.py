# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 09:20:38 2020

@author: - jtm

A python wrapper for some of the ledmotive RESTful API. 
See the "LIGHT HUB RESTful API" manuel for further functions and more info.

Make code simple, clear and without side-effects. Organise code sensibly. 
Use functions. 
"""
import requests
import random
from time import time, sleep
import matplotlib.pyplot as plt
import numpy as np

def setup_device(username, identity, password):
    '''
    Establish a connection to the device and return a device handle.

    Parameters
    ----------
    username : string
        the username provided by ledmotive
    identity : int
        an unique identity for the device
    password : string
        the password provided by ledmotive

    Returns
    -------
    device : dict
        this must be passed as an input argument when calling all other
        functions.
    '''
    url = '192.168.7.2' # IP address for USB-connected LIGHT HUB
    # LOGIN
    try:
        cmd_url = 'http://' + url + ':8181/api/login'
        a = requests.post(cmd_url, json={'username': username, 'password': password}, verify=False)
        cookiejar = a.cookies
        sleep(.1)
        device = {
            'url':url,
            'id':identity,
            'cookiejar':cookiejar
            }
    except requests.RequestException as err:
        print('login error: ', err)
    
    return device

def set_spectrum_a(device, intensity_values):
    '''
    Executes a spectrum based on the intensity values provided for each of the 
    channels. Each channel can be set between 0 and 4095 (only integer values).

    Parameters
    ----------
    device : dict
        device handle returned by setup_device()
    intensity_values : list
        list of 10 integer values between 0 and 4095

    Returns
    -------
    None.
    '''
    t1 = time()
    data = {"arg":intensity_values}
    cmd_url = "http://" + device['url'] + ":8181/api/luminaire/" + str(device['id']) + \
        "/command/SET_SPECTRUM_A"
    requests.post(cmd_url, cookies=device['cookiejar'], json=data, verify=False)
    t2 = time()
    print("set_spectrum_a exec time: {}".format(t2-t1))

def spectruma(device, intensity_values):
    '''
    Executes a spectrum based on the intensity values provided for each of the
    channels. Each channel can be set between 0 and 4095. This is an alternative 
    way to the command SET_SPECTRUM_A that allows setting a spectrum issuing a 
    GET command (which allows access to the luminaire by typing a url in any browser). 
    
    Parameters
    ----------
    device : dict
        device handle returned by setup_device()
    intensity_values : list
        list of 10 integer values between 0 and 4095

    Returns
    -------
    None.
    '''
    t1 = time()
    spec = ''.join([str(val) + ',' for val in intensity_values])[:-1]
    cmd_url = "http://" + device['url'] + ":8181/api/luminaire/" + str(device['id']) + \
        "/spectruma/" + spec
    requests.get(cmd_url, cookies=device['cookiejar'], verify=False)
    t2 = time()
    print("spectruma exec time: {}".format(t2-t1))
    
def color_xy(device, intensity_values, x, y):
    '''
    Similar to the "spectruma" command, but allows setting a target x, y
    coordinates in the CIE1931 color space. 

    Parameters
    ----------
    device : dict
        device handle returned by setup_device().
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
    t1 = time()
    spec = ''.join([str(val) + ',' for val in intensity_values])[:-1]
    cmd_url = "http://" + device['url'] + ":8181/api/luminaire/" + str(device['id']) + \
        "/spectruma/" + spec + "/color/" + str(x) + "/" + str(y)
    requests.get(cmd_url, cookies=device['cookiejar'], verify=False)
    t2 = time()
    print("color_xy exec time: {}".format(t2-t1))
    
def set_color(device, x, y, flux=None):
    '''
    Executes a light color represented in the CIE1931 color space. The x and y
    coordinates are the mathematical index that represents the target color to 
    be achieved. If the x,y provided values are not available by the system, 
    it will find its nearest available x,y coordinates. If flux is provided as
    an argument, it will be adjusted automatically, otherwise the current flux 
    will be used. 

    Parameters
    ----------
    device : dict
        device handle returned by setup_device().
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
    t1 = time()
    if flux:
        data = {"arg":[x, y, flux]}
    else:
        data = {"arg":[x, y]}
    cmd_url = "http://" + device['url'] + ":8181/api/luminaire/" + str(device['id']) + \
        "/command/SET_COLOR"
    requests.post(cmd_url, cookies=device['cookiejar'], json=data, verify=False)
    t2 = time()
    print("set_color exec time: {}".format(t2-t1))

def turn_off(device):
    '''
    Stops light emission by setting the power at all channels to 0.   
    
    Parameters
    ----------
    device : dict
        device handle returned by setup_device().

    Returns
    -------
    None.
    '''
    t1 = time()
    cmd_url = "http://" + device['url'] + ":8181/api/luminaire/" + str(device['id']) + \
        "/command/TURN_OFF"
    requests.post(cmd_url, cookies=device['cookiejar'], verify=False) 
    t2 = time()
    print("turn_off exec time: {}".format(t2-t1))

def set_blink(device, blink=1):
    '''
    Commands the luminaire to blink. The value provided as an argument is the
    number of times the light blinks in one second.

    Parameters
    ----------
    device : dict
        device handle returned by setup_device().
    blink : int, optional
        number of times the light should blink in one second. The default is 1.

    Returns
    -------
    None.
    '''
    t1 = time()
    data = {"arg":blink}
    cmd_url = "http://" + device['url'] + ":8181/api/luminaire/" + str(device['id']) + \
        "/command/SET_BLINK"
    requests.post(cmd_url, cookies=device['cookiejar'], json=data, verify=False) 
    t2 = time()
    print("set_blink exec time: {}".format(t2-t1))

def get_pcb_temperature(device):
    '''
    Returns the PCB temperature in Celsius degrees (ºC). Returns a list of 
    4 elements in this order: LEDs, Drivers, Spectrometer and Microcontroller 
    temperature sensors close to these elements. If one sensor or its readout 
    is not available a null value is returned for that element. 
    
    Parameters
    ----------
    device : dict
        device handle returned by setup_device().

    Returns
    -------
    temperatures : np.array
        [  Number,  Number,  Number,  Number  ].
    '''
    cmd_url = "http://" + device['url'] + ":8181/api/luminaire/" + str(device['id']) + \
        "/command/GET_PCB_TEMPERATURE"
    pcb = requests.get(cmd_url, cookies=device['cookiejar'], verify=False)
    temperatures = dict(pcb.json())["data"]
    
    return temperatures

def get_spectrometer_spectrum(device, norm=False):
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
    device : dict
        device handle returned by setup_device().

    Returns
    -------
    rmv : int
        the radiometric value
    spectrum : list
        [Number, Number, ..., Number, Number] with 81 elements
    '''
    cmd_url = "http://" + device['url'] + ":8181/api/luminaire/" + str(device['id']) + \
        "/command/GET_SPECTROMETER_SPECTRUM"
    data = requests.get(cmd_url, cookies=device['cookiejar'], verify=False) 
    
    rmv = dict(data.json())['data'][0]
    spectrum = np.array(dict(data.json())['data'][1:])
    
    if norm:
        return spectrum
    else:
        return spectrum * rmv

def get_led_calibration(device):
    '''
    Returns the current LED calibration matrix containing 10 rows 
    (for each channel) and 81 columns (intensity value from 380 to 780 nm 
    in steps of 5 nm).     

    Parameters
    ----------
    device : dict
        device handle returned by setup_device().

    Returns
    -------
    matrix : list
        10 x 81 calibration matrix.
    '''
    cmd_url = "http://" + device['url'] + ":8181/api/luminaire/" + str(device['id']) + \
        "/command/GET_LED_CALIBRATION"
    data = requests.get(cmd_url, cookies=device['cookiejar'], verify=False)   
    matrix = dict(data.json())["data"] 
    
    return matrix
    
def load_video_file(device, video):
    '''
    Uploads a video light sequence file to the LIGHT HUB. The video file must
    follow the LEDMOTIVE Dynamic Sequence File (.dsf) format. The uploaded file
    must be a json file (.dsf files are json files), and weight less than 2 MB.
    The file must be uploaded using the multipart/form-data standard convention 
    See play_video_file later about how to play the uploaded file in a luminaire.  

    Parameters
    ----------
    device : dict
        device handle returned by setup_device().
    video : string
        name of the video file.

    Returns
    -------
    None.
    '''
    t1 = time()
    args = [('file', (video, open(video, 'rb'), 'application/json'))]
    cmd_url = "http://" + device['url'] + ":8181/api/gateway/video" 
    requests.post(cmd_url, files=args, cookies=device['cookiejar'], verify=False)
    t2 = time()
    print("load_video_file exec time: {}".format(t2-t1))

def play_video_file(device, stop=False):
    '''
    Starts the execution of a light video sequence in the specified luminaire
    or multicast address. If no video is in the LIGHT HUB, an error response
    is raised, and the command ignored. If the video is already playing, the 
    play is interrupted, and the video is reproduced back from the beginning. 
    To stop the video, set 'stop' to True. See load_video_file for how to
    load a video file. 

    Parameters
    ----------
    device : dict
        device handle returned by setup_device().
    stop : bool, optional
        whether the command should stop the video. The default is False.

    Returns
    -------
    None.

    '''
    t1 = time()
    if stop:
        data = {'arg': None}
    else:
        data = {'arg': './data/video1.json'}
    cmd_url = "http://" + device['url'] + ":8181/api/luminaire/" + str(device['id']) + \
        "/command/PLAY_VIDEO_FILE"
    requests.post(cmd_url, json=data, cookies=device['cookiejar'], verify=False)
    t2 = time()
    print("play_video_file exec time {}".format(t2-t1))
    
def random_disco(device, nlights=10, blink=0):
    '''
    Start a random disco.

    Parameters
    ----------
    device : dict
        device handle returned by setup_device().
    nlights : int, optional
        number of random lights. The default is 10.
    blink : int, optional
        number of light blinks per second. The default is 0.

    Returns
    -------
    None.
    '''
    if blink:
        set_blink(device, blink)
    for i in range(nlights):
        intensity_values = [random.randrange(0, 4096) for val in range(10)]
        set_spectrum_a(device, intensity_values)
    set_blink(device, 0)
    turn_off(device)
    
def plot_spectrum(spectrum, color):
    bins = np.linspace(380,780,81)
    plt.plot(bins, spectrum, color=color)

    
    
    


    

    