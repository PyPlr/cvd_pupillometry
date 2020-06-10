# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 09:20:38 2020

@author: - JTM

A python wrapper for some of the ledmotive RESTful API. 
See the "LIGHT HUB RESTful API" manuel for further functions and more info.

Contains additional functions for working with the STLAB.
"""
import requests
import random
from time import time, sleep
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime
import json

########################################
# WRAPPER FOR FUNCTIONS IN RESTFUL API #
########################################

def setup_device(username='admin', identity=1, password='83e47941d9e930f6'):
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
        print("STLAB device setup complete.")
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
    #t1 = time()
    data = {"arg":intensity_values}
    cmd_url = "http://" + device['url'] + ":8181/api/luminaire/" + str(device['id']) + \
        "/command/SET_SPECTRUM_A"
    requests.post(cmd_url, cookies=device['cookiejar'], json=data, verify=False)
    #t2 = time()
    #print("set_spectrum_a exec time: {}".format(t2-t1))

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
    #t1 = time()
    spec = ''.join([str(val) + ',' for val in intensity_values])[:-1]
    cmd_url = "http://" + device['url'] + ":8181/api/luminaire/" + str(device['id']) + \
        "/spectruma/" + spec
    requests.get(cmd_url, cookies=device['cookiejar'], verify=False)
    #t2 = time()
    #print("spectruma exec time: {}".format(t2-t1))
    
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
    #t1 = time()
    spec = ''.join([str(val) + ',' for val in intensity_values])[:-1]
    cmd_url = "http://" + device['url'] + ":8181/api/luminaire/" + str(device['id']) + \
        "/spectruma/" + spec + "/color/" + str(x) + "/" + str(y)
    requests.get(cmd_url, cookies=device['cookiejar'], verify=False)
    #t2 = time()
    #print("color_xy exec time: {}".format(t2-t1))
    
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
    #t1 = time()
    if flux:
        data = {"arg":[x, y, flux]}
    else:
        data = {"arg":[x, y]}
    cmd_url = "http://" + device['url'] + ":8181/api/luminaire/" + str(device['id']) + \
        "/command/SET_COLOR"
    requests.post(cmd_url, cookies=device['cookiejar'], json=data, verify=False)
    #t2 = time()
    #print("set_color exec time: {}".format(t2-t1))

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
    #t1 = time()
    cmd_url = "http://" + device['url'] + ":8181/api/luminaire/" + str(device['id']) + \
        "/command/TURN_OFF"
    requests.post(cmd_url, cookies=device['cookiejar'], verify=False) 
    #t2 = time()
    #print("turn_off exec time: {}".format(t2-t1))

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
    #t1 = time()
    data = {"arg":blink}
    cmd_url = "http://" + device['url'] + ":8181/api/luminaire/" + str(device['id']) + \
        "/command/SET_BLINK"
    requests.post(cmd_url, cookies=device['cookiejar'], json=data, verify=False) 
    #t2 = time()
    #print("set_blink exec time: {}".format(t2-t1))

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
    #t1 = time()
    args = [('file', (video, open(video, 'rb'), 'application/json'))]
    cmd_url = "http://" + device['url'] + ":8181/api/gateway/video" 
    response = requests.post(cmd_url, files=args, cookies=device['cookiejar'], verify=False)
    if "data" not in response.json():
        raise "Upload file error"
    #t2 = time()
    #print("load_video_file exec time: {}".format(t2-t1))
    return response.json()

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
    #t1 = time()
    if stop:
        data = {'arg': None}
    else:
        data = {'arg': './data/video1.json'}
    cmd_url = "http://" + device['url'] + ":8181/api/luminaire/" + str(device['id']) + \
        "/command/PLAY_VIDEO_FILE"
    requests.post(cmd_url, json=data, cookies=device['cookiejar'], verify=False)
    #t2 = time()
    #print("play_video_file exec time {}".format(t2-t1))

#################################
# FUNCTIONS TO MAKE VIDEO FILES #
#################################

def get_header(df, repeats=1):
    
    header_dict = {
            "version":"1",
            "model":"VEGA10",
            "channels":10,
            "spectracount":len(df),
            "transitionsCount":len(df),
            "fluxReference":0,
            "repeats":repeats
            }

    return header_dict

def get_metadata(df, creator='jtm'):
    
    meta_dict = {
            "creationTime":str(datetime.now()),
            "creator":creator
            }

    return meta_dict

def get_spectra(df):
    
    light_cols = df.columns[1:]
    return df[light_cols].values.tolist()

def get_transitions(df):
    
    list_of_dicts = []
    
    for index , row in df.iterrows():
        
        list_of_dicts.append({
            "spectrum":index,
            "power":100,
            "time":int(row['time']),
            "flags":0})
    
    return list_of_dicts

def make_video_file(df, video_nm, repeats=1):
    ''' 
    Reads in a CSV file with columns 'time' , 'primary-1'...'primary-10'
    and returns a json file compatible with spectratune lab device
    '''
      
    d = {
        "header":get_header(df, repeats),
        "metadata":get_metadata(df),
        "spectra":get_spectra(df),
        "transitions":get_transitions(df)
        }
    
    with open(video_nm + '.dsf', 'w') as outfile:
        json.dump(d, outfile)
        
    return json.dumps(d)

###################################################
# ADDITIONAL FUNCTIONS FOR WORKING WITH THE STLAB #
###################################################
    
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

def sample_leds(device, leds=[0], intensity=[4095], wait_before_sample=.2):
    """
    Sample each of the given LEDs at the specified intensity settings.

    Parameters
    ----------
    device : dict
        device handle returned by setup_device().
    leds : list, optional
        list of leds to sample. The default is [0].
    intensity : list, optional
        The intensity values to use for the sampling. The default is [4095].
    wait_before_sample : float, optional
        Time in seconds to wait after setting a spectrum before acquiring 
        measurement from spectrometer. The default is .2.

    Returns
    -------
    df : DataFram
        The resulting DataFrame with hierarchial pd.MultiIndex and column "flux".

    """
        
    print("Sampling {} leds at the following intensities: {}".format(len(leds), intensity))
    bins = np.linspace(380,780,81)
    leds_off = [0]*10
    
    # dict to store data
    df = pd.DataFrame()
    midx = pd.MultiIndex.from_product([leds, intensity, bins], names=['led', 'intensity', 'wavelength'])

    # turn stlab off if it's on
    set_spectrum_a(device, leds_off)

    for led in leds:
        set_spectrum_a(device, leds_off)
        sleep(wait_before_sample)
        for val in intensity:
            print("Led: {}, intensity: {}".format(led, val))
            spec = [0]*10
            spec[led] = val
            set_spectrum_a(device, spec)
            sleep(wait_before_sample)
            data = get_spectrometer_spectrum(device, norm=False)
            data = pd.DataFrame(data)
            data.rename(columns={0:'flux'}, inplace=True)
            df = pd.concat([df, pd.DataFrame(data)])
    
    turn_off(device)
    df.index = midx
    return df  

def interp_spectra(spectra):
    """
    This function needs generalising.

    Parameters
    ----------
    spectra : TYPE
        DESCRIPTION.

    Returns
    -------
    intp_tbl : TYPE
        DESCRIPTION.

    """
    
    tbl = spectra.unstack(level=2)
    tbl.columns = [val[1] for val in tbl.columns]
    
    intp_tbl = pd.DataFrame()
    for led, df in tbl.groupby(["led"]):
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

def predicted_spd(intensity=[0,0,0,0,0,0,0,0,0,0], lkp_table=None): # not working atm
    """
    Predict the spectral power distribution for a given list of led 
    intensities using linear interpolation.

    Parameters
    ----------
    intensity : list
        List of intensity values for each led. The default is [0,0,0,0,0,0,0,0,0,0].
    lkp_table : DataFrame
        A wide-format DataFrame with hierarchichal pd.MultIndex [led, intensity] 
        and a column for each of 81 5-nm wavelength bins. 4096*10 rows, containing
        predicted for each led at all possible intensities.

    Returns
    -------
    spectrum : np.array
        Predicted spectrum for given intensities.

    """
    spectrum = np.zeros(81)
    for led , val in enumerate(intensity):
        spectrum += lkp_table.loc[(led,val)].to_numpy()
    return spectrum

def get_led_colors():
    colors = ['blueviolet', 'royalblue', 'darkblue',
              'blue', 'cyan', 'green', 'lime',
              'orange','red','darkred']
    return colors


def spec_to_xyz(spec):
    """Convert a spectrum to an xyz point.

    The spectrum must be on the same grid of points as the colour-matching
    function, cmf: 380-780 nm in 5 nm steps.

    """
    from CIE import get_CIE_CMF
    
    cmf = get_CIE_CMF()[1:]
    cmf = cmf.T
    XYZ = np.sum(spec[:, np.newaxis] * cmf, axis=0)
    den = np.sum(XYZ)
    if den == 0.:
        return XYZ
    return XYZ / den

def spectra_to_xyz(spectra):
    """
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
    """
    
    idx = []    
    xyz = []
    for i, spec in spectra.groupby(by=["led","intensity"]):
        idx.append(i)
        xyz.append(spec_to_xyz(spec["flux"].to_numpy()))
    xyz = pd.DataFrame(xyz, columns=["X","Y","Z"])
    xyz.index = pd.MultiIndex.from_tuples(idx, names=['led','intensity'])
    return xyz

def spectra_to_peak_wavelengths(spectra):
    """
    Calculate the peak wavelengths for a given set of spectra.

    Parameters
    ----------
    spectra : TYPE
        DESCRIPTION.

    Returns
    -------
    pwl : TYPE
        DESCRIPTION.

    """
    idx = []    
    pwl = []
    for i, spec in spectra.groupby(by=["led","intensity"]):
        idx.append(i)
        pwl.append(spec.loc[spec["flux"]==spec["flux"].max(), "wavelength"].to_numpy()) 
    pwl = pd.DataFrame(pwl, columns=["wavelength"])
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
    dwl = pd.DataFrame(dwl, columns=["wavelength"])
    dwl.index = pd.MultiIndex.from_tuples(idx, names=['led','intensity'])
    return dwl

def spectra_to_melanopic_irradiance(spectra):
    from CIE import get_CIES026
    
    # get melanopsin sensitivity
    _ , sss = get_CIES026(asdf=True)
    mel = sss["Mel"]
    mel = mel[::5]
    
    # aggregate to melanopic irradiance
    mi = spectra.groupby(by=['led','intensity'])['flux'].agg(lambda x: x.dot(mel.values.T))
    return mi

def explore_spectra(spectra):
    """
    This function takes a DataFrame of spectra and plots them, along with other
    useful info.
    """
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
        ax[i, 0].set_xlabel("Wavelength $\lambda$ (nm)")
        ax[i, 0].set_ylabel("Flux (mW)")
    
        # plot color coordinates
        plot_chromaticity_diagram_CIE1931(standalone=False, axes=ax[i, 1], title=False, show_spectral_locus=False)
        ax[i, 1].set_xlim((-.15,.9))
        ax[i, 1].set_ylim((-.1,1))
        ax[i, 1].scatter(xyz.loc[i,"X"], xyz.loc[i,"Y"], c='k', s=3)
        
        # plot peak and dominant wavelength as a function of input
        inpt = spectra["intensity"] / 4095
        inpt = np.linspace(0, 1, len(spectra.intensity.unique()))
        ax[i, 2].plot(inpt, pwl.loc[i, 'wavelength'], color=colors[i], lw=1, label='Peak')
        ax[i, 2].set_xlabel("Input")
        
        ax[i, 2].plot(inpt, dwl.loc[i, 'wavelength'], color=colors[i], lw=3, label='Dominant')
        ax[i, 2].set_xlabel("Input")
        ax[i, 2].set_ylabel("$\lambda$ (nm)")
        low  = dwl.loc[i, 'wavelength'].min()-dwl.loc[i, 'wavelength'].min()*0.1
        high = dwl.loc[i, 'wavelength'].max()+dwl.loc[i, 'wavelength'].max()*0.1
        ax[i, 2].set_ylim((low, high))
        ax[i, 2].legend()
        
        # plot melanopic irradience
        ax[i, 3].plot(inpt, mi.loc[i], color=colors[i])
        ax[i, 3].set_ylim((0,14000))
        ax[i, 3].set_xlabel("Input")
        ax[i, 3].set_ylabel("Melanopic irradiance (mW)")
    
    return fig    