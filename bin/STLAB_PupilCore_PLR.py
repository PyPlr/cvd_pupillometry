#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep  7 13:06:12 2020

@author: jtm
"""

from time import time, sleep

from pyplr.stlab import SpectraTuneLab
from pyplr.pupil import PupilCore
from pyplr.stlabhelp import pulse_protocol
from pyplr.utils import unpack_data_pandas

# Configure params
PULSE_SPEC = [100] * 10  # Low intensity pulse with all channels
PULSE_DURATION = 1000  # ms
RECORDING_NAME = "my_recording"


def main():
    try:

        # Connect to pupil core and set time to current
        p = PupilCore()
        p.command(f"T {time()}")

        # Authenticate with STLAB
        d = SpectraTuneLab.from_config()

        # Make video file
        pulse_protocol(
            pulse_spec=PULSE_SPEC, duration=PULSE_DURATION, fname="1s_pulse"
        )

        # Load the video file
        _ = d.upload_video("video1.dsf")

        # Start a new recording called "my_recording"
        p.command(f"R {RECORDING_NAME}")

        # Wait a few seconds
        sleep(2)

        # Make an annotation for when the light comes on
        annotation = p.new_annotation("LIGHT_ON")

        # Start the .light_stamper(...) and .pupil_grabber(...)
        lst_future = p.light_stamper(annotation=annotation, timeout=10)
        pgr_future = p.pupil_grabber(topic="pupil.1.3d", seconds=10)

        # Play
        d.play_video_file("video1.dsf")

        # Wait for the futures
        while lst_future.running() or pgr_future.running():
            print("Waiting for futures...")
            sleep(1)

        # Get the timestamp and pupil data
        timestamp = lst_future.result()[1]
        data = unpack_data_pandas(pgr_future.result())

        # Plot the PLR
        ax = data["diameter_3d"].plot()
        ax.axvline(x=timestamp, color="k")

    except KeyboardInterrupt:
        print("> Experiment terminated by user.")

    finally:
        p.command("r")
        print("> Stopped recording in Pupil Capture.")
        d.stop_video()
        d.turn_off()
        d.logout()
        print("> Logging out of STLAB.")


if __name__ == "__main__":
    main()
