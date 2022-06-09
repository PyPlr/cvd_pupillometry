#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pyplr.stlab
===========

A python wrapper for Ledmotive's Spectra Tune Lab light engine and RESTful API.
Most documentation comes from the 'LIGHT HUB RESTful API' manual, so please
consult this for further functions and more info. Note that a license is
required to develop against the RESTful API.

"""

import os.path as op
from pathlib import Path
from typing import List, Tuple, Union
from time import sleep

import requests
from requests import Response
import numpy as np
from pyplr.CIE import get_CIE170_2_chromaticity_coordinates
from pyplr.stlabhelp import video_file_to_dict


class LightHubError(Exception):
    pass


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
    def __init__(self,
                 password: str,
                 username: str = 'admin',
                 default_address: int = 1,
                 lighthub_ip: str = '192.168.7.2') -> None:
        """Initialize connection with LightHub.

        Parameters
        ----------
        password : string
            The password specific to the LightHub.
        username : string
            The username for logging in. The default is 'admin'.
        default_address : int
            Commands will target this address unless a specific address is
            provided when a command is issued. The default is `1`.
        lightub_ip : string, optional
            The IP address of the LightHub device. The default is
            `'192.168.7.2'`. On Mac and Linux, this may need to be changed to
            `'192.168.6.2'`.

        Note
        ----
        Luminaires have an address assigned automatically when they are
        registered by the LIGHT HUB. This address is used to issue requests to
        that particular luminaire and is referred to within this documentation
        simply as *address*. Whenever an *address* is required, a multicast
        address can be used instead. See `set_multicast_address(...)` to know
        more how to configure multicast addresses.

        Luminaires sharing the same multicast address are considered a group,
        and where this documentation refers to *group #*, it should be read as
        all the luminaires sharing the multicast address #. A special multicast
        address, `1023`, known as the broadcast address, is reserved to refer
        to all the luminaires in the installation.

        Addresses should be within the range 1 and 1022 (reserving 1023 as the
        broadcast address). The LIGHT HUB registers new luminaires assigning
        them the lowest address available. Luminaire addresses are shared with
        multicast addresses, which means a luminaire cannot have an address
        already in use as a multicast address.

        Do not mix luminaires with a different quantity of channels in the same
        group as this might lead to unexpected behavior, particularly when
        using functions with parameters dependent in the luminaire number of
        channels.

        When GET commands are issued using the broadcast address, `1023`, or
        any multicast address, the return value will be from whichever device
        replies first. To avoid ambiguity, GET commands should therefore target
        a unique device address.

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

        try:
            response = self.login(password=self.password,
                                  username=self.username,
                                  lighthub_ip=self.lighthub_ip)
            cookiejar = response.cookies

        except requests.RequestException as err:
            print('Login error: ', err)

        else:
            self.info = {
                'url': self.lighthub_ip,
                'default_address': default_address,
                'cookiejar': cookiejar,
            }
            addresses = [val['address'] for val in self.get_luminaires()]
            print('LIGHT HUB login success')
            print(f'User authenticated as: {self.username}')
            print(f'The following addresses are defined: {addresses}')
            print('Call get_luminaires() / get_device_info() for more info')

        finally:
            pass
        
    @classmethod
    def from_config(cls):
        """Initialise connection using config file in home directory.
        
        The file must be called .stlabconfig and have the following structure:
            
            password ***************
            username admin
            default_address 1
            lighthub_ip 192.168.6.2
            
        Returns
        -------
        SpectraTuneLab instance
        
        Raises
        ------
        FileNotFoundError if .stlabconfig does not exist

        """
        home = op.expanduser('~')
        conf_file = op.abspath(op.join(home, '.stlabconfig'))
        try:
            with open(conf_file, 'r') as f:
                for line in f.readlines(): 
                    if 'password' in line:
                        password = line.split()[1] 
                    if 'username' in line:
                        username = line.split()[1] 
                    if 'default_address' in line:
                        default_address = line.split()[1] 
                    if 'lighthub_ip' in line:
                        lighthub_ip = line.split()[1] 
            return cls(password, username, default_address, lighthub_ip)
        
        except FileNotFoundError as err:
            raise err('.stlabconfig is not there...')
            
    # Response checkers
    def _check_response_for_error(self, response: Response) -> Response:
        """Catch and raise errors from LIGHT HUB, if present."""
        if 'error' in response.json():
            raise LightHubError(response.json()['error'])
        else:
            return response

    def _check_response_for_data(self, response: Response) -> Response:
        """Raise AttributeError if data is not present (when expected)."""
        try:
            return response.json()['data']
        except:
            err = 'No data in the response. Check connection / command.'
            raise AttributeError(err)

    # Adress checker
    def _get_address(self, address: int = None):
        """Get string address for command target."""
        if address is None:
            return str(self.default_address)
        else:
            return str(address)

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

    # Functions wrapped from STLAB's RESTFUL_API (with relevant documentation)
    def login(self, password: str, username: str = 'admin',
              lighthub_ip: str = '192.168.7.2') -> Response:
        """Authenticates the user into the LIGHT HUB.

        Note that specific username and password varies from device to device.
        This password shall be provided by LEDMOTIVE in case the LIGHT HUB was
        distributed with password protection. **Authentication is required** to
        use the rest of the API endpoints, unless the LIGHT HUB is publicly
        accessible (without password authentication). In any case note the use
        of a **password is not a security measure** and shall be regarded only
        as a user management tool. To enforce security in the device encrypted
        connections must be established using HTTPS connections, which are not
        enabled by default and requires the installation of a TLS certificate
        in the device provided by a certification entity for each specific
        LIGHT HUB, and would require Internet access of the device to the
        certification entity.

        Parameters
        ----------
        username : string
            Username for logging in. The default is 'admin'.
        password : string
            The password specific to the LightHub.
        lightub_ip : string, optional
            The IP address of the LightHub device. The default is
            `'192.168.7.2'`. On Mac and Linux, this may need to be changed to
            `'192.168.6.2'`.

        Returns
        -------
        requests.Response

        """
        cmd_url = 'http://' + self.lighthub_ip + ':8181/api/login'
        data = {'username': username, 'password': password}
        response = requests.post(cmd_url, json=data, verify=False)
        return self._check_response_for_error(response)

    def logout(self) -> Response:
        """Terminates the user authentication session in the API.

        Returns
        -------
        requests.Response

        """
        cmd_url = 'http://' + self.lighthub_ip + ':8181/api/logout'
        response = requests.post(cmd_url, verify=False)
        return self._check_response_for_error(response)

    def get_luminaires(self) -> List[dict]:
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
        response = self._check_response_for_error(response)
        return self._check_response_for_data(response)

    def set_spectrum_a(self, intensity_values: List[int],
                       address: int = None) -> Response:
        """Executes a spectrum based on the intensity values provided for each
        of the channels. Each channel can be set between 0 and 4095 (only
        integer values).

        Parameters
        ----------
        intensity_values : list
            List of 10 integer values between 0 and 4095.
        address : int
            Send the command to this address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        requests.Response

        """
        address = self._get_address(address)
        data = {'arg': intensity_values}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/SET_SPECTRUM_A'
        response = requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)
        return self._check_response_for_error(response)

    def set_spectrum_s(self, spectrum: List[int],
                       address: int = None) -> Response:
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
            Send the command to this address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        requests.Response

        See Also
        --------
        ``pyplr.stlabhelp.make_spectrum_s``

        """
        address = self._get_address(address)
        data = {'arg': spectrum}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/SET_SPECTRUM_S'
        response = requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)
        return self._check_response_for_error(response)

    def spectruma(self, intensity_values: List[int],
                  address: int = None) -> Response:
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
            Send the command to this address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        requests.Response

        """
        address = self._get_address(address)
        spec = ''.join([str(val) + ',' for val in intensity_values])[:-1]
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/spectruma/' + spec
        response = requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        return self._check_response_for_error(response)

    def color_xy(self, intensity_values: List[int], x: float, y: float,
                 address: int = None) -> Response:
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
            Send the command to this address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        requests.Response

        """
        address = self._get_address(address)
        spec = ''.join([str(val) + ',' for val in intensity_values])[:-1]
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/spectruma/' + spec + '/color/' + \
            str(x) + '/' + str(y)
        response = requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        return self._check_response_for_error(response)

    def set_color(self, x: float, y: float, flux: int = None,
                  address: int = None) -> Response:
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
            Send the command to this address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        requests.Response

        """
        address = self._get_address(address)
        if flux:
            data = {'arg': [x, y, flux]}
        else:
            data = {'arg': [x, y]}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/SET_COLOR'
        response = requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)
        return self._check_response_for_error(response)

    def turn_off(self, address: int = None) -> Response:
        """Stops light emission by setting the power at all channels to 0.

        Parameters
        ----------
        address : int
            Send the command to this address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        requests.Response

        """
        address = self._get_address(address)
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/TURN_OFF'
        response = requests.post(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        return self._check_response_for_error(response)

    def turn_on(self, address: int = None) -> Response:
        """The luminaire resumes emitting light using last known spectrum.

        The default spectrum is used if none is known or it was all 0s. See
        `set_spectrum_a(...)`.

        Parameters
        ----------
        address : int
            Send the command to this address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        requests.Response

        """
        address = self._get_address(address)
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/TURN_ON'
        response = requests.post(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        return self._check_response_for_error(response)

    def set_blink(self, blink: int = 0, address: int = None) -> Response:
        """Commands the luminaire to blink. The value provided as an argument
        is the number of times the light blinks in one second.

        Parameters
        ----------
        blink : int, optional
            Number of times the light should blink in one second. Value must be
            between 0-255. The default is 1.
        address : int
            Send the command to this address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        requests.Response

        Raises
        ------
        ValueError if blink < 0 or blink > 255

        """
        if blink < 0 or blink > 255:
            raise ValueError('Blink must be in range 0-255')
        address = self._get_address(address)
        data = {'arg': blink}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/SET_BLINK'
        response = requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)
        return self._check_response_for_error(response)

    def get_pcb_temperature(self, address: int = None) -> List:
        """Returns the PCB temperature in Celsius degrees (ºC).

        Returns a list of 4 elements in this order: LEDs, Drivers, Spectrometer
        and Microcontroller temperature sensors close to these elements. If one
        sensor or its readout is not available a null value is returned for
        that element.

        Parameters
        ----------
        address : int
            Send the command to this address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        temperatures : list
            [Number, Number, Number, Number].

        """
        address = self._get_address(address)
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/GET_PCB_TEMPERATURE'
        response = requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        response = self._check_response_for_error(response)
        return self._check_response_for_data(response)

    def get_spectrum_a(self, address: int = None) -> List:
        """Returns the current amplitude for each of the luminaire channels.

        The array returned has a length equal to the channel count of the
        luminaire. Each value in the array is a representation of electrical
        counts, ranging from 0 to 4095 counts.

        Parameters
        ----------
        address : int
            Send the command to this address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        List
            Intensity values for luminaire channels.

        """
        address = self._get_address(address)
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/GET_SPECTRUM_A'
        response = requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        response = self._check_response_for_error(response)
        return self._check_response_for_data(response)

    def get_spectrometer_spectrum(
            self, norm: bool = False,
            address: int = None) -> Tuple[float, np.array]:
        """Returns the spectrum readout from the internal spectrometer.

        If the luminaire does only contain a colorimeter sensor, a theoretical
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
            Send the command to this address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        rmv : float
            Radiometric value.
        spectrum : np.array
            [Number, Number, ..., Number, Number] with 81 elements.

        """
        address = self._get_address(address)
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/GET_SPECTROMETER_SPECTRUM'
        response = requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        data = self._check_response_for_data(response)
        rmv = data[0]
        spectrum = np.array(data[1:])
        if norm:
            return rmv, spectrum
        else:
            return rmv, spectrum * rmv

    def get_lumens(self, address: int = None) -> int:
        """Returns the luminous flux by the luminaire in lumens. Lumens are
        the total quantity of visible light emitted by a source (this is a
        radiant flux weighted against the human eye's sensitivity).

        Parameters
        ----------
        address : int
            Send the command to this address. Leave as `None` to target the
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
        return self._check_response_for_data(response)

    def get_led_calibration(self, address: int = None) -> List:
        """Returns the current LED calibration matrix containing 10 rows
        (for each channel) and 81 columns (intensity value from 380 to 780 nm
        in steps of 5 nm).

        Parameters
        ----------
        address : int
            Send the command to this address. Leave as `None` to target the
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
        return self._check_response_for_data(response)

    def load_video_file(self,
                        fname: str,
                        return_vf_dict: bool = True) -> Union[dict, None]:
        """Uploads a video light sequence file to the LIGHT HUB. The video
        file must follow the LEDMOTIVE Dynamic Sequence File (.dsf) format.
        The uploaded file must be a json file (.dsf files are json files),
        with weight less than 2 MB. The file must be uploaded using the
        multipart / form-data standard convention. See ``play_video_file(...)``
        for how to play the uploaded file in a luminaire.

        Parameters
        ----------
        fname : string
            Name of the video file.

        Returns
        -------
        dict if `return_vf_dict==True` else None.

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

    def download_video_file(self) -> dict:
        """Downloads the video file currently recorded in the LIGHT HUB.

        Raises
        ------
        LightHubError
            If the response has no data.

        Returns
        -------
        dict
            The video file.

        """
        cmd_url = 'http://' + self.info['url'] + ':8181/api/gateway/video'
        response = requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        try:
            return response.json()
        except:
            raise LightHubError('No data.')

    def play_video_file(self, fname: str, address: int = None) -> Response:
        """Starts the execution of a light video sequence in the specified
        luminaire or multicast address. If no video is in the LIGHT HUB, an
        error response is raised, and the command ignored. If the video is
        already playing, the play is interrupted, and the video is reproduced
        back from the beginning. See `load_video_file(...)` for how to load a
        video file.

        Parameters
        ----------
        fname : string
            Name of the video file.
        address : int
            Send the command to this address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        requests.Response

        """
        address = self._get_address(address)
        data = {'arg': fname}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/PLAY_VIDEO_FILE'
        response = requests.post(
            cmd_url, json=data, cookies=self.info['cookiejar'], verify=False)
        response = self._check_response_for_error(response)
        print(f'Playing video file at address: {address}')
        return response

    def stop_video(self, address: int = None) -> Response:
        """Stops the video being played for this luminaire address.

        This command is a convenient alias for PLAY_VIDEO_FILE with a *null*
        target file. The command does nothing if no video is being played.

        Parameters
        ----------
        address : int
            Send the command to this address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Note
        ----
        When playing video files from the LIGHT HUB a different video might be
        played at the same time for each multicast address of the luminaire.

        This command only stops the video being played for the address
        specified as luminaire address. If other videos are being played on
        another multicast address, or the broadcast address, for this
        luminaire, those videos are not stopped.

        This behavior is required for current implementation (videos are played
        from the LIGHT HUB) and might change in the future (if videos are
        played from the luminaire itself) to make this command stop all the
        videos regardless of address. Additionally, we might add an extra
        argument to specify the "id" of which exact video to stop.

        Returns
        -------
        requests.Response

        """
        address = self._get_address(address)
        data = {'arg': None}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/PLAY_VIDEO_FILE'
        response = requests.post(
            cmd_url, json=data, cookies=self.info['cookiejar'], verify=False)
        response = self._check_response_for_error(response)
        print(f'Stopped video file from playing at address: {address}')
        return response

    def get_video_playing(self, address: int = None) -> dict:
        """Check if a video is being played for the targeted luminaire address.

        Return its video id if available.

        Parameters
        ----------
        address : int
            Send the command to this address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        dict
            Dict with the video id and a Boolean value informing on whether a
            video is being played or not.

        """
        address = self._get_address(address)
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/GET_VIDEO_PLAYING'
        response = requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        return self._check_response_for_data(response)

    def clear_video_cache(self, address: int = 1023) -> Response:
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
            Send the command to this address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        requests.Response

        """
        address = self._get_address(address)
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/CLEAR_VIDEO_CACHE'
        response = requests.post(
            cmd_url, json={}, cookies=self.info['cookiejar'], verify=False)
        if 'error' in response.json():
            raise LightHubError(response.json()['error'])
        else:
            print('Cleared video cache...')
            return response

    def get_device_info(self, address: int = None) -> dict:
        """Returns the device characteristics and basic configuration. These
        are the serial code, the model code, the number of channels for this
        luminaire and the device feedback type (whether it is colorimeter or
        spectrometer). How are the serial and model codes is yet to be defined,
        but expect a maximum 50 character length code for serial and 30 for
        model.

        Parameters
        ----------
        address : int
            Send the command to this address. Leave as `None` to target the
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
        return self._check_response_for_data(response)

    def set_colour_priority(self, colour_priority: bool = True,
                            address: int = None) -> Response:
        """Command the luminaire to always first approximate to the desired
        color of the spectrum to set before setting the spectrum channel
        values. This function is set to true or false (enabled or disabled).

        Parameters
        ----------
        colour_priority : bool
            Whether to enable or disable colour priority.
        address : int
            Send the command to this address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        requests.Response

        """
        address = self._get_address(address)
        data = {'arg': colour_priority}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/SET_COLOR_PRIORITY'
        response = requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)
        return self._check_response_for_error(response)

    def get_colour_priority(self, address: int = None) -> bool:
        """Get current color priority configuration for this luminaire.

        Parameters
        ----------
        address : int
            Send the command to this address. Leave as `None` to target the
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
        return self._check_response_for_data(response)

    def set_use_feedback(self, use_feedback: bool,
                         address: int = None) -> Response:
        """Command the luminaire to use the feedback sensor to maintain the
        color through the PID algorithm. this function is set to true or false
        (enabled or disabled).

        Parameters
        ----------
        address : int
            Send the command to this address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        requests.Response

        """
        address = self._get_address(address)
        data = {'arg': use_feedback}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/SET_USE_FEEDBACK'
        response = requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)
        return self._check_response_for_error(response)

    def get_use_feedback(self, address: int = None) -> bool:
        """Get current use feedback configuration for this luminaire.

        Parameters
        ----------
        address : int
            Send the command to this address. Leave as `None` to target the
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
        return self._check_response_for_data(response)

    def get_spectrometer_integration_time(self,
                                          address: int = None) -> int:
        """Get the current integration time used by the spectrometer for
        gathering data.

        Parameters
        ----------
        address : int
            Send the command to this address. Leave as `None` to target the
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
        return self._check_response_for_data(response)

    def set_spectrometer_integration_time(
            self, integration_time: int, address: int = None) -> Response:
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
            Send the command to this address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        requests.Response

        """
        address = self._get_address(address)
        data = {'arg': integration_time}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/SET_SPECTROMETER_INTEGRATION_TIME'
        response = requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)
        return self._check_response_for_error(response)

    def get_input_power(self, address: int = None) -> int:
        """Returns the current consumed electrical power of the luminaire in
        mW.

        Parameters
        ----------
        address : int
            Send the command to this address. Leave as `None` to target the
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
        return self._check_response_for_data(response)

    def set_dimming_level(self, dimming_level: int,
                          address: int = None) -> Response:
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
            Send the command to this address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        requests.Response

        """
        address = self._get_address(address)
        data = {'arg': dimming_level}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/SET_DIMMING_LEVEL'
        response = requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)
        return self._check_response_for_error(response)

    def get_dimming_level(self, address: int = None) -> int:
        """Returns the user intensity dimmer. See `set_dimming_level(...)` for
        more info.

        Parameters
        ----------
        address : int
            Send the command to this address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        int
            Current percentage dimming level.

        """
        address = self._get_address(address)
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/GET_DIMMING_LEVEL'
        response = requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        return self._check_response_for_data(response)

    def set_multicast_address(
            self,
            address: int = None,
            multicast_address: List[Union[int, None]] = [999, None, None, None]
    ) -> Response:
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
            Send the command to this address.
        multicast_address : list, optional
            Multicast address to set for the device. The default is
            [999, None, None, None].

        Returns
        -------
        requests.Response

        """
        data = {'arg': multicast_address}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            str(address) + '/command/SET_MULTICAST_ADDRESS'
        response = requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)
        return self._check_response_for_error(response)

    def get_multicast_address(
            self, address: int = None) -> List[Union[int, None]]:
        """Returns the array of multicast addresses set in the luminaire. See
        `.set_multicast_address(...)` for more info.

        Parameters
        ----------
        address : int
            Send the command to this address. Leave as `None` to target the
            default address (i.e., `self.default_address`).

        Returns
        -------
        list
            e.g., `[999, None, None, None]`
        """
        address = self._get_address(address)
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/' + \
            address + '/command/GET_MULTICAST_ADDRESS'
        response = requests.get(
            cmd_url, cookies=self.info['cookiejar'], verify=False)
        return self._check_response_for_data(response)

    def get_video_file_metadata(self, fname: str) -> dict:
        """Retrieve metadata for video file on LIGHT HUB.

        Before a video can be played, the file must be parsed and loaded into
        memory. This process can be specially slow, particularly for larger
        video files. Because of this, the LIGHT HUB comes with a caching
        mechanism that maintains the last 5 launched videos into memory,
        greatly speeding subsequent calls to play the video.

        It is possible to force the LIGHT HUB to parse and load a video in its
        cache without actually starting to play it by requesting the video
        metadata. By doing this with the videos we later want to launch, we can
        obtain a faster response at play time and ease the synchronization of
        the videos, specially for the initial frames.

        It is important to note this preloading strategy needs to be repeated
        each time the LIGHT HUB is turned off or it is reseted.

        Parameters
        ----------
        fname : str
            The video file name, e.g., video1.json.

        Returns
        -------
        dict
            The metadata.

        """
        data = {'arg': fname}
        cmd_url = 'http://' + self.info['url'] + ':8181/api/luminaire/1023' + \
            '/command/GET_VIDEO_FILE_METADATA'
        response = requests.post(
            cmd_url, cookies=self.info['cookiejar'], json=data, verify=False)
        return self._check_response_for_data(response)
