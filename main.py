from argparse import ArgumentParser
from dataclasses import dataclass
from math import ceil
from pathlib import Path
from sys import stderr

from mido import MidiFile, Message

parser = ArgumentParser(description="Turns a MIDI file into a lot of "
                                    "TypeScript code for MakeCode Arcade!")
parser.add_argument("path", type=Path,
                    help="The path to the MIDI file. ")
parser.add_argument("--output_path", type=Path,
                    default=None, help="The path to write the code to")
parser.add_argument("--stdout", action="store_const",
                    const=True, default=False,
                    help="Whether to output everything to standard output "
                         "instead of writing to a file")
args = parser.parse_args()

in_path = args.path.expanduser().resolve()
out_path = args.output_path
to_stdout = args.stdout
if out_path is None:
    # Put output file in the same directory as input file with same name
    # but with different extension
    out_path = in_path.parent / (in_path.stem + ".txt")


def log(msg: str):
    if not to_stdout:
        print(msg)


def err(msg: str):
    stderr.write(msg)


log(f"Parsing {in_path}")
midi = MidiFile(in_path)

if midi.type not in (0, 1):
    err(f"MIDI file not type 0 or type 1!")
    exit(1)

log(f"MIDI file type: {midi.type}")

# Generate all MIDI messages in playback order
# This will squish all tracks together
msgs = tuple(midi)


@dataclass
class NextChordResult:
    notes: list[Message]
    ending_index: int
    time: float


def find_next_chord(index: int) -> NextChordResult:
    """
    Gathers notes from the current index into a list until we hit a note that
    has non-zero time.

    :param index: The index to start looking at.
    :return: A NextChordResult dataclass.
    """
    chord_notes = []
    chord_end_index = index
    chord_time = 0
    for i in range(index, len(msgs)):
        cur_msg = msgs[i]
        if cur_msg.type == "note_on" and cur_msg.velocity > 0:
            chord_notes.append(cur_msg)
        if cur_msg.time > 0 or cur_msg.type != "note_on":
            chord_end_index = i
            chord_time = cur_msg.time
            break
    return NextChordResult(chord_notes, chord_end_index, chord_time)


def find_time_of_note(index: int) -> float:
    """
    Finds the duration of a note.

    :param index: The index of the note.
    :return: The duration of note, in seconds.
    """
    note_time = 0
    for i in range(index, len(msgs)):
        cur_msg = msgs[i]
        note_time += cur_msg.time
        if cur_msg.type == "note_on" and \
                cur_msg.velocity == 0 and \
                cur_msg.note == msgs[index].note:
            break
    return note_time


def note_num_to_name(num: int) -> str:
    # https://stackoverflow.com/a/54546263/10291933
    notes = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]
    octave = ceil(num / 12)
    name = notes[num % 12]
    return name + str(octave)


i = 0
while i < len(msgs):
    msg = msgs[i]
    if msg.type == "note_on":
        result = find_next_chord(i)
        if len(result.notes) > 0:
            log(f"Chord of {len(result.notes)} with duration {result.time}s:")
            for note in result.notes:
                log(f"  - {note_num_to_name(note.note - 21)} at "
                    f"velocity {note.velocity} for "
                    f"{find_time_of_note(i)}s")
        i = result.ending_index + 1
    else:
        log(f"Meta message: {msg}")
        i += 1
