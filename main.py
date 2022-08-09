import logging
from argparse import ArgumentParser
from collections import Counter
from dataclasses import dataclass
from math import ceil
from pathlib import Path
from sys import stdout, stderr

from mido import MidiFile, Message

parser = ArgumentParser(description="Turns a MIDI file into a lot of "
                                    "TypeScript code for MakeCode Arcade!")
parser.add_argument("path", type=Path,
                    help="The path to the MIDI file. ")
parser.add_argument("--output_path", "-p", type=Path,
                    default=None, help="The path to write the code to.")
parser.add_argument("--stdout", "-s", action="store_true",
                    help="Whether to output everything to standard output "
                         "instead of writing to a file. ")
parser.add_argument("--debug", "-d", action="store_true",
                    help="Whether to log debug messages or not. ")
args = parser.parse_args()

in_path = args.path.expanduser().resolve()
out_path = args.output_path
debug = args.debug
to_stdout = args.stdout
if out_path is None:
    # Put output file in the same directory as input file with same name
    # but with different extension
    out_path = in_path.parent / (in_path.stem + ".txt")


def create_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """
    A simple function to create a logger. You would typically put this right
    under all the other modules you imported.
    And then call `logger.debug()`, `logger.info()`, `logger.warning()`,
    `logger.error()`, `logger.critical()`, and
    `logger.exception` everywhere in that module.
    :param name: A string with the logger name.
    :param level: A integer with the logger level. Defaults to logging.DEBUG.
    :return: A logging.Logger which you can use as a regular logger.
    """
    logger = logging.getLogger(name=name)
    logger.setLevel(level=level)
    logger.propagate = False

    console_formatter = logging.Formatter("%(asctime)s - %(name)s - "
                                          "%(levelname)s - %(message)s")

    # https://stackoverflow.com/a/16066513/10291933
    stdout_handler = logging.StreamHandler(stream=stdout)
    stdout_handler.setLevel(level=level)
    stdout_handler.addFilter(lambda record: record.levelno <= logging.INFO)
    stdout_handler.setFormatter(fmt=console_formatter)
    if stdout_handler not in logger.handlers:
        logger.addHandler(hdlr=stdout_handler)

    stderr_handler = logging.StreamHandler(stream=stderr)
    stderr_handler.setLevel(level=logging.WARNING)
    stderr_handler.setFormatter(fmt=console_formatter)
    if stderr_handler not in logger.handlers:
        logger.addHandler(hdlr=stderr_handler)

    logger.debug(f"Created logger named {repr(name)} with level {repr(level)}")
    logger.debug(f"Handlers for {repr(name)}: {repr(logger.handlers)}")
    return logger


if to_stdout:
    level = logging.WARNING
elif debug:
    level = logging.DEBUG
else:
    level = logging.INFO
logger = create_logger(__name__, level=level)

logger.info(f"Parsing {in_path}")
midi = MidiFile(in_path)

if midi.type not in (0, 1):
    raise ValueError(f"MIDI file not type 0 or type 1!")

logger.debug(f"MIDI file type: {midi.type}")

# Generate all MIDI messages in playback order
# This will squish all tracks together
msgs = tuple(midi)


def note_num_to_name(num: int) -> str:
    # https://stackoverflow.com/a/54546263/10291933
    notes = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]
    octave = ceil(num / 12)
    name = notes[num % 12]
    return name + str(octave)


# https://gist.github.com/CGrassin/26a1fdf4fc5de788da9b376ff717516e
# MIT License
# Python to convert a string note (eg. "A4") to a frequency (eg. 440).
# Inspired by https://gist.github.com/stuartmemo/3766449
def get_frequency(note: str, A4: int = 440) -> float:
    """
    Get the frequency from a note name.

    :param note: A note name, ex. "A4"
    :param A4: The frequency of note A4. Defaults to 440. (hz)
    :return: A float of the frequency.
    """
    notes = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]
    octave = int(note[2]) if len(note) == 3 else int(note[1])
    key_number = notes.index(note[0:-1])
    if key_number < 3:
        key_number = key_number + 12 + ((octave - 1) * 12) + 1
    else:
        key_number = key_number + ((octave - 1) * 12) + 1
    return A4 * 2 ** ((key_number - 49) / 12)


logger.info("Generating code")

code = """"""

for msg in msgs:
    if msg.type == "note_on":
        logger.debug(f"Note message: {msg}")
    else:
        logger.debug(f"Meta message: {msg}")

if to_stdout:
    print(code)
else:
    logger.info(f"Writing to {out_path}")
    out_path.write_text(code)
