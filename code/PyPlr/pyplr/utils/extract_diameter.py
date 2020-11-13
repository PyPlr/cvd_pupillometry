import argparse
import csv
import logging
import os
import traceback as tb

import numpy as np
import msgpack


logger = logging.getLogger(__name__)


def main(recordings, csv_out, overwrite=False):
    """Process given recordings one by one
    Iterates over each recording and handles cases where no pupil.pldata or
    pupil_timestamps.npy files could be found.
    recordings: List of recording folders
    csv_out: CSV file name under which the result will be saved
    """
    for rec in recordings:
        try:
            logger.info("Extracting {}...".format(rec))
            process_recording(rec, csv_out, overwrite=overwrite)
        except FileNotFoundError:
            logger.warning(
                (
                    "The recording {} did not include any prerecorded pupil files!"
                ).format(rec)
            )
            logger.debug(tb.format_exc())


def process_recording(recording, csv_out, overwrite=False):
    """Process a single recording
    recordings: List of recording folders
    csv_out: CSV file name under which the result will be saved
    overwrite: Boolean indicating if an existing csv file should be overwritten
    """
    csv_out_path = os.path.join(recording, csv_out)
    if os.path.exists(csv_out_path):
        if not overwrite:
            logger.warning("{} exists already! Not overwriting.".format(csv_out_path))
            return
        else:
            logger.warning("{} exists already! Overwriting.".format(csv_out_path))

    with open(csv_out_path, "w") as csv_file:
        writer = csv.writer(csv_file, dialect=csv.unix_dialect)
        writer.writerow(csv_header())

        extracted_rows = load_and_yield_data(recording)
        writer.writerows(extracted_rows)


def csv_header():
    """CSV header fields"""
    return (
        "eye_id",
        "timestamp",
        "topic",
        "confidence",
        "diameter_2d [px]",
        "diameter_3d [mm]",
    )


def load_and_yield_data(directory, topic="pupil"):
    """Load and extract pupil diameter data
    See the data format documentation[2] for details on the data structure.
    Adapted open-source code from Pupil Player[1] to read pldata files.
    Removed the usage of Serialized_Dicts since this script has the sole purpose
    of running through the data once.
    [1] https://github.com/pupil-labs/pupil/blob/master/pupil_src/shared_modules/file_methods.py#L137-L153
    [2] https://docs.pupil-labs.com/#data-files
    """
    ts_file = os.path.join(directory, topic + "_timestamps.npy")
    data_ts = np.load(ts_file)

    msgpack_file = os.path.join(directory, topic + ".pldata")
    with open(msgpack_file, "rb") as fh:
        unpacker = msgpack.Unpacker(fh, raw=False, use_list=False)
        for timestamp, (topic, payload) in zip(data_ts, unpacker):
            datum = deserialize_msgpack(payload)

            # custom extraction function for pupil data, see below for details
            eye_id, conf, dia_2d, dia_3d = extract_eyeid_diameters(datum)

            # yield data according to csv_header() sequence
            yield (eye_id, timestamp, topic, conf, dia_2d, dia_3d)


def extract_eyeid_diameters(pupil_datum):
    """Extract data for a given pupil datum
    
    Returns: tuple(eye_id, confidence, diameter_2d, and diameter_3d)
    """
    return (
        pupil_datum["id"],
        pupil_datum["confidence"],
        pupil_datum["diameter"],
        pupil_datum.get("diameter_3d", 0.0),
    )


def deserialize_msgpack(msgpack_bytes):
    """Deserialize msgpack[1] data
    [1] https://msgpack.org/index.html
    """
    return msgpack.unpackb(msgpack_bytes, raw=False, use_list=False)


if __name__ == "__main__":
    # setup logging
    logging.basicConfig(level=logging.DEBUG)

    # setup command line interface
    parser = argparse.ArgumentParser(
        description=(
            "Extract 2d and 3d (if available) "
            "pupil diameters for a set of given recordings. "
            "The resulting csv file will be saved within its "
            "according recording."
        )
    )
    parser.add_argument(
        "--out",
        help="CSV file name containing the extracted data",
        default="extracted_diameter.csv",
    )
    parser.add_argument(
        "-f",
        "--overwrite",
        action="store_true",
        help=(
            "Usually, the command refuses to overwrite existing csv files. "
            "This flag disables these checks."
        ),
    )
    parser.add_argument("recordings", nargs="+", help="One or more recordings")

    # parse command line arguments and start the main procedure
    args = parser.parse_args()
    main(recordings=args.recordings, csv_out=args.out, overwrite=args.overwrite)