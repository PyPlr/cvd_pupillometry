#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pyplr.stlab
===========

A python wrapper for Ledmotive's Spectra Tune Lab light engine and RESTful API.
See the 'LIGHT HUB RESTful API' manual for further functions and more info.
Note that a license is required to develop against the RESTful API.

"""

from typing import List, Any
from time import sleep
from pprint import pprint

import requests
import numpy as np
from pyplr.CIE import get_CIE170_2_chromaticity_coordinates
from pyplr.stlabhelp import video_file_to_dict


class SpectraTuneLab:
    """Wrapper for LEDMOTIVE Spectra Tune Lab REST API.

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
    >>> d = SpectraTuneLab(username='admin', default_address=1, password='*')
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
    >>> d = SpectraTuneLab(username='admin', default_address=1, password='*')
    >>> d.load_video_file('my_video_file')
    >>> d.play_video_file()

    """
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
    def __init__(self, password, username='admin', default_address=1,
                 lighthub_ip='192.168.7.2'):
        """Initialize connection with LightHub.

        Parameters
        ----------
        username : string
            The username for logging in.
        default_address : int
            A unique numerical identifier for the device. All commands will
            target this address if a specific address is not given when the
            command is issued. The default `1`.
        password : string
            The password specific to the LightHub.
        lightub_ip : string, optional
            The IP address of the LightHub device. The default is
            `'192.168.7.2'`.

        Note
        ----
        When GET commands are issued using the broadcast address, `1023`, or
        any multicast address, the return value will be from whichever device
        replies first. To avoid ambiguity, GET commands should therefore target
        a unique device address.

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

        """
        self.username = username
        self.default_address = default_address
        self.password = password
        self.lighthub_ip = lighthub_ip
        self.info = {}

        try:
            cmd_url = 'http://' + self.lighthub_ip + ':8181/api/login'
            response = requests.post(cmd_url,
                                     json={'username': username,
                                           'password': password},
                                     verify=False)
            cookiejar = response.cookies
            sleep(.1)
            self.info = {
                'url': self.lighthub_ip,
                'default_address': default_address,
                'cookiejar': cookiejar}

            # For some reason, after first turning on the STLAB, video files
            # won't play unless you first do something in synchronous mode. A
            # quick call to spectruma at startup gets around this issue, but
            # it might be a good idea to ask Ledmotive about this. Also, the
            # first time you do play a video file, it often flickers.
            # USE MULTICAST ADDRESS!
            self.spectruma([0, 0, 0, 0, 0, 0, 0, 0, 1, 1])
            sleep(.2)
            self.turn_off()
            print('STLAB device setup complete...')
            pprint(self.get_luminaires())

        except requests.RequestException as err:
            print('login error: ', err)

    # Demos
    def demo(self, mode):

        if mode == 1:
            for led in range(10):
                spec = [0] * 10
                spec[led] = 1000
                self.set_spectrum_a(spec)
                sleep(1)

        elif mode == 2:
            xy = get_CIE170_2_chromaticity_coordinates()
            for idx, row in xy.iterrows():
                print(f'x={row.x}, y={row.y}')
                self.set_color(row.x, row.y, flux=1000)

        self.turn_off()

    # Method to get the address for a command
    def _get_address(self, address=None):
        if address is None:
            return str(self.default_address)
        else:
            return str(address)

    # Functions wrapped from STLAB's RESTFUL_API (with relevant documentation)
    def get_luminaires(self):
        """Get a list of registered luminaires and groups for this LIGHT HUB
        with detailed information for each of them.

        Key:

            * `address`: Id number of the luminaire or group
            * `channel_count`: Number of channels
            * `feedback`: If true activate the optical feedback
            * `sensor`: If its value is 1 the spectrometer is being used. If
              its  value is 2 the colorimeter is being used.
            * `match_xy`: If true the color has priority over the spectrum.
            * `group`: If true this is not a luminaire but a multicast group.
            * `serial`: The serial id of the luminaire
            * `devices`: If this element is a group, this property is an array
              with the address of all luminaires in the group.

        Returns
        -------
        list of dict
            List of dicts with information related to the connected luminaires.

        """
        cmd_url = 'http://' + self.info['url'] + ':8181/api/gateway/luminaires'
        response = requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        return dict(response.json())['data']

    def set_spectrum_a(self, intensity_values: List[int],
                       address: int = None) -> Any:
        """Executes a spectrum based on the intensity values provided for each
        of the channels. Each channel can be set between 0 and 4095 (only
        integer values).

        Parameters
        ----------
        intensity_values : list
            List of 10 integer values between 0 and 4095.
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        None.
            None.

        """
        address = self._get_address(address)
        data = {'arg': intensity_values}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/SET_SPECTRUM_A'
        return requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)

    def set_spectrum_s(self, spectrum: List[int],
                       address: int = None) -> Any:
        """Executes the given spectrum. The spectrum is defined by an array of
        81 elements that represents 5 nm wavelength bins from 380 nm to 780 nm.
        The values are an abstraction of the light intensity at each point
        that allows the reconstruction of the spectrum shape. Each value ranges
        between 0 and 65535, 0 being no intensity and 65535 being full
        intensity at the corresponding wavelength bin (prior application of
        dimming and power protection caps).

        Parameters
        ----------
        spectrum : list
            List of 81 (the 380 nm to 780 nm bins) integer values between
            0 and 65535.
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        None.
            None.

        See Also
        --------
        ``pyplr.stlabhelp.make_spectrum_s``

        """
        address = self._get_address(address)
        data = {'arg': spectrum}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/SET_SPECTRUM_S'
        return requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)

    def spectruma(self, intensity_values: List[int],
                  address: int = None) -> Any:
        """Executes a spectrum based on the intensity values provided for each
        of the channels. Each channel can be set between 0 and 4095. This is an
        alternative way to the command `set_spectrum_a` that allows setting a
        spectrum issuing a `GET` command (which allows access to the luminaire
        by typing a url in any browser).

        Parameters
        ----------
        intensity_values : list
            List of 10 integer values between 0 and 4095.
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        None.
            None.

        """
        address = self._get_address(address)
        spec = ''.join([str(val) + ',' for val in intensity_values])[:-1]
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/spectruma/' + spec
        return requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)

    def color_xy(self, intensity_values: List[int], x: float, y: float,
                 address: int = None) -> Any:
        """Similar to the `spectruma` command, but allows setting a target
        `x, y` coordinates in the CIE1931 color space.

        Parameters
        ----------
        intensity_values : list
            The desired spectrum as a list of integers.
        x : float
            Desired target CIE1931 `x` coordinate as a decimal number.
        y : float
            Desired target CIE1931 `y` coordinate as a decimal number.
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        None.
            None.

        """
        address = self._get_address(address)
        spec = ''.join([str(val) + ',' for val in intensity_values])[:-1]
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/spectruma/' + spec + '/color/' + \
            str(x) + '/' + str(y)
        return requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)

    def set_color(self, x: float, y: float, flux: int = None,
                  address: int = None) -> Any:
        """Executes a light color represented in the CIE1931 color space. The
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
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        None.
            None.

        """
        address = self._get_address(address)
        if flux:
            data = {'arg': [x, y, flux]}
        else:
            data = {'arg': [x, y]}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/SET_COLOR'
        return requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)

    def turn_off(self, address: int = None) -> Any:
        """Stops light emission by setting the power at all channels to 0.

        Parameters
        ----------
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        None.
            None.

        """
        address = self._get_address(address)
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/TURN_OFF'
        return requests.post(
            cmd_url, cookies=self.info['cookiejar'], verify=False)

    def set_blink(self, blink: int = 1, address: int = None) -> Any:
        """Commands the luminaire to blink. The value provided as an argument
        is the number of times the light blinks in one second.

        Parameters
        ----------
        blink : int, optional
            Number of times the light should blink in one second. The default
            is 1.
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        None.
            None.

        """
        address = self._get_address(address)
        data = {'arg': blink}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/SET_BLINK'
        return requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)

    def get_pcb_temperature(self, address: int = None) -> np.array:
        """Returns the PCB temperature in Celsius degrees (ºC). 
        
        Returns a list of 4 elements in this order: LEDs, Drivers, Spectrometer 
        and Microcontroller temperature sensors close to these elements. If one
        sensor or its readout is not available a null value is returned for
        that element.

        Parameters
        ----------
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        temperatures : np.array
            [Number, Number, Number, Number].

        """
        address = self._get_address(address)
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/GET_PCB_TEMPERATURE'
        response = requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        temperatures = dict(response.json())['data']
        return temperatures

    def get_spectrum_a(self, address: int = None) -> Any:
        """Returns the current amplitude for each of the luminaire channels.
        
        The array returned has a length equal to the channel count of the
        luminaire. Each value in the array is a representation of electrical
        counts, ranging from 0 to 4095 counts.

        Parameters
        ----------
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        None.
            None.

        """
        address = self._get_address(address)
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/GET_SPECTRUM_A'
        response = requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        return np.array(dict(response.json())['data'][1:])

    def get_spectrometer_spectrum(
            self, norm: bool = False, address: int = None) -> Any:
        """Returns the spectrum readout from the internal spectrometer. If the
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
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        spectrum : list
            [Number, Number, ..., Number, Number] with 81 elements.

        """
        address = self._get_address(address)
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/GET_SPECTROMETER_SPECTRUM'
        response = requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        rmv = dict(response.json())['data'][0]
        spectrum = np.array(dict(response.json())['data'][1:])
        if norm:
            return rmv, spectrum
        return rmv, spectrum * rmv

    def get_lumens(self, address: int = None) -> Any:
        """Returns the luminous flux by the luminaire in lumens. Lumens are
        the total quantity of visible light emitted by a source (this is a
        radiant flux weighted against the human's eye sensitivity).

        Parameters
        ----------
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        lumens : int
            Intensity of light measured in lumens.

        """
        address = self._get_address(address)
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/GET_LUMENS'
        response = requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        return dict(response.json())['data']

    def get_led_calibration(self, address: int = None) -> Any:
        """Returns the current LED calibration matrix containing 10 rows
        (for each channel) and 81 columns (intensity value from 380 to 780 nm
        in steps of 5 nm).

        Parameters
        ----------
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        matrix : list
            10 x 81 calibration matrix.

        """
        address = self._get_address(address)
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/GET_LED_CALIBRATION'
        response = requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        return dict(response.json())['data']

    # TODO: check video file stuff against API
    def load_video_file(self, fname: str, return_vf_dict: bool = True) -> Any:
        """Uploads a video light sequence file to the LIGHT HUB. The video
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

        """
        args = [('file', (fname, open(fname, 'rb'), 'application/json'))]
        cmd_url = 'http://' + self.info['url'] + ':8181/api/gateway/video'
        response = requests.post(
            cmd_url, files=args, cookies=self.info['cookiejar'], verify=False)
        if 'data' not in response.json():
            raise 'Upload file error'
        print('video file loaded...')
        if return_vf_dict:
            return video_file_to_dict(fname)

    def play_video_file(self, stop: bool = False,
                        address: int = None) -> Any:
        """Starts the execution of a light video sequence in the specified
        luminaire or multicast address. If no video is in the LIGHT HUB, an
        error response is raised, and the command ignored. If the video is
        already playing, the play is interrupted, and the video is reproduced
        back from the beginning. To stop the video, use `stop=True`. See
        `load_video_file(...)` for how to load a video file.

        Parameters
        ----------
        stop : bool, optional
            Whether the command should stop the video. The default is False.
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        None.
            None.

        """
        address = self._get_address(address)
        if stop:
            data = {'arg': None}
        else:
            data = {'arg': './data/video1.json'}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/PLAY_VIDEO_FILE'
        print('playing video file...')
        return requests.post(
            cmd_url, json=data, cookies=self.info['cookiejar'], verify=False)

    def clear_video_cache(self, address: int = 1023):
        """Clears all videos cached into the gateway memory.
        
        By default each time a video is played using the PLAY_VIDEO_FILE 
        command, the video file is opened, parsed and loaded into memory. 
        Because this is a blocking and time consuming I/O operation, the loaded
        video is cached into memory so successive calls require virtually no 
        time to load the video. In contrast loading a 2 MB video for play can 
        take up to 1.5 seconds. Up to 8 videos are cached at all times, 
        dropping the least recently used ones when needed.

        Parameters
        ----------
        address : int, optional
            Luminaire address. The default is 1023 (the broadcast address).

        Returns
        -------
        {}
            Empty object or an error.

        """
        address = self._get_address(address)
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/CLEAR_VIDEO_CACHE'
        print('Cleared video cache...')
        response = requests.post(
            cmd_url, json={}, cookies=self.info['cookiejar'], verify=False)
        if 'error' in response.json():
            with response.json()['error'] as e:
                print(e)
        else: 
            return response

    def get_device_info(self, address: int = None) -> Any:
        """Returns the device characteristics and basic configuration. These
        are the serial code, the model code, the number of channels for this
        luminaire and the device feedback type (whether it is colorimeter or
        spectrometer). How are the serial and model codes is yet to be defined,
        but expect a maximum 50 character length code for serial and 30 for
        model.

        Parameters
        ----------
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        dict
            The device info.

        """
        address = self._get_address(address)
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/GET_DEVICE_INFO'
        response = requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        return dict(response.json())['data']

    def set_colour_priority(self, colour_priority: bool = True,
                            address: int = None) -> Any:
        """Command the luminaire to always first approximate to the desired
        color of the spectrum to set before setting the spectrum channel
        values. This function is set to true or false (enabled or disabled).

        Parameters
        ----------
        colour_priority : bool
            Whether to enable or disable colour priority.
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        None.
            None.

        """
        address = self._get_address(address)
        data = {'arg': colour_priority}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/SET_COLOR_PRIORITY'
        return requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)

    def get_colour_priority(self, address: int = None) -> Any:
        """Get current color priority configuration for this luminaire.

        Parameters
        ----------
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        colour_priority : bool
            Whether colour priority is enabled.

        """
        address = self._get_address(address)
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/GET_COLOR_PRIORITY'
        response = requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        return dict(response.json())['data']

    def set_use_feedback(self, use_feedback: bool,
                         address: int = None) -> Any:
        """Command the luminaire to use the feedback sensor to maintain the
        color through the PID algorithm. this function is set to true or false
        (enabled or disabled).

        Parameters
        ----------
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        None.
            None.

        """
        address = self._get_address(address)
        data = {'arg': use_feedback}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/SET_USE_FEEDBACK'
        return requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)

    def get_use_feedback(self, address: int = None) -> Any:
        """Get current use feedback configuration for this luminaire.

        Parameters
        ----------
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        use_feedback : bool
            Whether use feedback is enabled.

        """
        address = self._get_address(address)
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/GET_USE_FEEDBACK'
        response = requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        return dict(response.json())['data']

    def get_spectrometer_integration_time(self,
                                          address: int = None) -> int:
        """Get the current integration time used by the spectrometer for
        gathering data.

        Parameters
        ----------
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        integration_time : int
            A positive integer ranging from 50 to 140000 in tenths of
            millisecond.

        """
        address = self._get_address(address)
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/GET_SPECTROMETER_INTEGRATION_TIME'
        response = requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        return dict(response.json())['data']

    def set_spectrometer_integration_time(
            self, integration_time: int, address: int = None) -> Any:
        """Sets the integration time of the spectrometer to gather data. Longer
        times will result in more light reaching the sensor (like exposure
        time in photography). Special attention should be taken to avoid
        signal saturation.

        Parameters
        ----------
        integration_time : int
            A positive integer ranging from 50 to 140000 in tenths of
            millisecond.
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        None.
            None.

        """
        address = self._get_address(address)
        data = {'arg': integration_time}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/SET_SPECTROMETER_INTEGRATION_TIME'
        return requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)

    def get_input_power(self, address: int = None) -> Any:
        """Returns the current consumed electrical power of the luminaire in
        mW.

        Parameters
        ----------
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        input_power : int
            The electrical power at the luminaire in mW.

        """
        address = self._get_address(address)
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/GET_INPUT_POWER'
        response = requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        return dict(response.json())['data']

    def set_dimming_level(self, dimming_level: int,
                          address: int = None) -> Any:
        """Sets an intensity dimmer. This percentage modulates the current
        intensity by multiplying the power count of each luminaire channel,
        i.e. if you send a spectrum where each channel count is at half level
        and the dimming is set at 50%, the final light intensity will be one
        quarter of the luminaire full capacity.

        Parameters
        ----------
        dimming_level : int
            Percentage dimming level.
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        None.
            None.

        """
        address = self._get_address(address)
        data = {'arg': dimming_level}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/SET_DIMMING_LEVEL'
        return requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)

    def get_dimming_level(self, address: int = None) -> Any:
        """Returns the user intensity dimmer. See `set_dimming_level(...)` for
        more info.

        Parameters
        ----------
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        None.
            None.

        """
        address = self._get_address(address)
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/GET_DIMMING_LEVEL'
        response = requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        return dict(response.json())['data']

# TODO: check everything below here
    def set_multicast_address(
            self,
            address: int = None,
            multicast_address: List[int] = [1001, None, None, None]) -> Any:
        """Sets an array of multicast addresses accepted by the luminaire. A
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
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).
        multicast_address : list, optional
            Multicast address to set for the device. The default is
            [1001, None, None, None].

        Returns
        -------
        None.

        """
        data = {'arg': multicast_address}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            str(address) + '/command/SET_MULTICAST_ADDRESS'
        return requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)

    def get_multicast_address(self, address: int = None) -> Any:
        """Returns the array of multicast addresses set in the luminaire. See
        `.set_multicast_address(...)` for more info.

        Parameters
        ----------
        address : int
            Send the command to this address. Either a unique device
            address (e.g. `1`, `2`, etc.), the broadcast address (i.e., 1023),
            or a custom multicast address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        None.
            None.

        """
        address = self._get_address(address)
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/GET_MULTICAST_ADDRESS'
        response = requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        return dict(response.json())['data']

    def get_video_file_metadata(self, fname):
        data = {'arg': fname}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/1023' + \
            '/command/GET_VIDEO_FILE_METADATA'
        response = requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)
        return response
