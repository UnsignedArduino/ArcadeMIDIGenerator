import logging
from argparse import ArgumentParser
from math import ceil
from pathlib import Path
from sys import stdout, stderr

from mido import MidiFile

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

code = """namespace ArcadeMIDI {
    let DEBUG_PARSING: boolean = false;
    let DEBUG_PLAYING: boolean = false;

    export function log(parsing: boolean, playing: boolean, console_on_screen: boolean): void {
        DEBUG_PARSING = parsing;
        DEBUG_PLAYING = playing;
        game.consoleOverlay.setVisible(console_on_screen);
    }

    export namespace ArcadeMIDIInternals {
        interface ArcadeMIDINote {
            frequency: number;
            velocity: number;
        };

        // All stolen from @richard on the MakeCode Forums:
        // https://forum.makecode.com/t/announcement-makecode-arcade-mini-game-jam-2-submission-thread/14534/11?u=unsignedarduino

        //% shim=music::queuePlayInstructions
        function queuePlayInstructions(timeDelta: number, buf: Buffer) { }

        export class ArcadeMIDISound {
            /**
             * Formats and writes to a provided buffer the neccessary information to play a note.
             * 
             * @param sndInstr The buffer to store the instruction in. 
             * @param sndInstrPtr Index of where to start writing in the buffer.
             * @param ms How long for the sound to last, in milliseconds.
             * @param beg The beginning velocity.
             * @param end The ending velocity.
             * @param The sound wave type.
             * @param hz The hertz of the sound.
             * @param volume The velocity overall.
             * @param endHz The ending hertz of the sound.
             * @return The index of where we ended writing to the buffer.
             */
            private addNote(sndInstr: Buffer, sndInstrPtr: number, ms: number, beg: number, end: number, soundWave: number, hz: number, volume: number, endHz: number): number {
                if (ms > 0) {
                    sndInstr.setNumber(NumberFormat.UInt8LE, sndInstrPtr, soundWave);
                    sndInstr.setNumber(NumberFormat.UInt8LE, sndInstrPtr + 1, 0);
                    sndInstr.setNumber(NumberFormat.UInt16LE, sndInstrPtr + 2, hz);
                    sndInstr.setNumber(NumberFormat.UInt16LE, sndInstrPtr + 4, ms);
                    sndInstr.setNumber(NumberFormat.UInt16LE, sndInstrPtr + 6, (beg * volume) >> 6);
                    sndInstr.setNumber(NumberFormat.UInt16LE, sndInstrPtr + 8, (end * volume) >> 6);
                    sndInstr.setNumber(NumberFormat.UInt16LE, sndInstrPtr + 10, endHz);
                    sndInstrPtr += 12;
                }
                sndInstr.setNumber(NumberFormat.UInt8LE, sndInstrPtr, 0); // terminate
                return sndInstrPtr;
            }

            /**
             * Create and queue an instruction to play.
             * 
             * @param when When to play the instruction, in milliseconds.
             * @param frequency The frequency of the sound in hertz.
             * @param velocity The velocity of the sound.
             * @param ms The duration of the sound in milliseconds.
             */
            public playNoteCore(when: number, frequency: number, velocity: number, ms: number): void {
                let buf = control.createBuffer(12);

                // const amp = Math.min(Math.abs(currentSpeed) / PLAY_SPEED, 1) * 255;
                const amp = 255;

                this.addNote(buf, 0, ms, amp, amp, 1, frequency, velocity, frequency);
                queuePlayInstructions(when, buf);
            }
        }

        export class ArcadeMIDIInstructions {
            private _sound_driver: ArcadeMIDISound = undefined;
            private _playing_notes: ArcadeMIDINote[] = [];

            public constructor() {
                this._sound_driver = new ArcadeMIDISound();
                this._playing_notes = [];
            }

            /**
             * Converts a note number (0 - 88, on a piano) to the actual note name.
             * 
             * @param num The note number.
             * @return The note name.
             */
            private note_num_to_name(num: number): string {
                // https://stackoverflow.com/a/54546263/10291933
                const notes: string[] = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"];
                const octave = Math.ceil(num / 12);
                const name = notes[num % 12];
                return name + octave.toString();
            }

            /**
             * Converts a note name into the frequency. 
             * 
             * @param note The note name. (example: "A4")
             * @param A4 The frequency A4 should be at, in hertz. Defaults to 440 hertz.
             * @return The frequency, in hertz.
             */
            private get_frequency(note: string, A4: number = 440): number {
                // https://gist.github.com/CGrassin/26a1fdf4fc5de788da9b376ff717516e
                // MIT License
                // Python to convert a string note(eg. "A4") to a frequency(eg. 440).
                // Inspired by https://gist.github.com/stuartmemo/3766449
                const notes: string[] = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"];
                const octave: number = parseInt(note.length === 3 ? note[2] : note[1]);
                let key_number: number = notes.indexOf(note.slice(0, note.length - 1));
                if (key_number < 3) {
                    key_number = key_number + 12 + ((octave - 1) * 12) + 1;
                } else {
                    key_number = key_number + ((octave - 1) * 12) + 1;
                }
                return A4 * 2 ** ((key_number - 49) / 12);
            }

            /**
             * "note_on" MIDI command.
             * 
             * @param note_index The MIDI note index.
             * @param velocity The velocity to play the note at. Set to 0 to stop playing the note.
             * @param time The time to delay afterwards, in milliseconds.
             * @param play_now Whether to actually queue the notes to play now or not. Defaults to true. 
             */
            public note_on(note_index: number, velocity: number, time: number, play_now: boolean = true): void {
                const frequency: number = this.get_frequency(this.note_num_to_name(note_index - 21));
                if (velocity == 0) {
                    for (let i = 0; i < this._playing_notes.length; i++) {
                        if (this._playing_notes[i].frequency == frequency) {
                            this._playing_notes.splice(i, 1);
                            break;
                        }
                    }
                } else {
                    this._playing_notes.push(<ArcadeMIDINote>{ frequency: frequency, velocity: velocity });
                }
                if (time > 0 && play_now) {
                    this.play_now(time);
                    pause(time);
                }
            }

            /**
             * Replays all the notes for a certain period of time.
             * 
             * @param duration The duration to play all the playing notes.
             */
            public play_now(duration: number) {
                if (DEBUG_PLAYING) {
                    console.log(`Playing ${this._playing_notes.length} frequencies`);
                }
                for (const note of this._playing_notes) {
                    this._sound_driver.playNoteCore(0, note.frequency, note.velocity, duration);
                };
            }
        }
    }

    export namespace ArcadeMIDIImageParser {
        export class ArcadeMIDIImageFrame {
            private _img_ref: Image;
            private _start_y: number;
            private _stop_y: number;

            private _duration_start_y: number;
            private _duration_stop_y: number;
            private _velocity_start_y: number;
            private _velocity_stop_y: number;
            private _note_start_y: number;
            private _note_stop_y: number;

            private _frame_len: number;

            public constructor(img_ref: Image, start_y: number, stop_y: number) {
                this._img_ref = img_ref;
                this._start_y = start_y;
                this._stop_y = stop_y;
                this.recompute_frame(DEBUG_PARSING);
            }

            /**
             * Gets the reference image.
             * 
             * @return An image.
             */
            get image_ref(): Image {
                return this._img_ref;
            }

            /**
             * Gets the frame length.
             * 
             * @return A number, the width of the image - 2.
             */
            get frame_length(): number {
                return this._frame_len;
            }

            /**
             * Recomputes the frame from the image.
             * Note: This will parse the image to recompute neccessary information, and may take a long time.
             * 
             * @param debug Whether to log what we find. 
             */
            private recompute_frame(debug: boolean = false): void {
                let duration_start_y: number | undefined = undefined;
                let duration_stop_y: number | undefined = undefined;
                let velocity_start_y: number | undefined = undefined;
                let velocity_stop_y: number | undefined = undefined;
                let note_start_y: number | undefined = undefined;
                let note_stop_y: number | undefined = undefined;

                const frame_x: number = 1;

                const note_color: number = 1;  // White
                const velocity_color: number = 2;  // Red
                const duration_color: number = 3;  // Pink

                const log = (s: string) => {
                    if (debug) {
                        console.log(s);
                    }
                };

                for (let y = this._start_y; y <= this._stop_y; y++) {
                    const prev_px = this._img_ref.getPixel(frame_x, y - 1);
                    const curr_px = this._img_ref.getPixel(frame_x, y);
                    const next_px = this._img_ref.getPixel(frame_x, y + 1);

                    if (prev_px != curr_px) {  // Starting new color
                        switch (curr_px) {
                            case (note_color): {
                                note_start_y = y;
                                log(`Found note start at ${y}`);
                                break;
                            }
                            case (velocity_color): {
                                velocity_start_y = y;
                                log(`Found velocity start at ${y}`);
                                break;
                            }
                            case (duration_color): {
                                duration_start_y = y;
                                log(`Found duration start at ${y}`);
                                break;
                            }
                            default: {
                                log(`Found unknown start at ${y}`);
                                break;
                            }
                        }
                    } else if (next_px != curr_px) {  // Ending new color
                        switch (curr_px) {
                            case (note_color): {
                                note_stop_y = y;
                                log(`Found note end at ${y}`);
                                break;
                            }
                            case (velocity_color): {
                                velocity_stop_y = y;
                                log(`Found velocity end at ${y}`);
                                break;
                            }
                            case (duration_color): {
                                duration_stop_y = y;
                                log(`Found duration end at ${y}`);
                                break;
                            }
                            default: {
                                log(`Found unknown end at ${y}`);
                                break;
                            }
                        }
                    }
                }

                this._duration_start_y = duration_start_y;
                this._duration_stop_y = duration_stop_y;
                this._velocity_start_y = velocity_start_y;
                this._velocity_stop_y = velocity_stop_y;
                this._note_start_y = note_start_y;
                this._note_stop_y = note_stop_y;

                this._frame_len = this._img_ref.width - 2;
            }

            /**
             * Get the hex value from the image, most significant byte first on top.
             * 
             * @param x The x value in the image.
             * @param start_y The starting y value in the image.
             * @param stop_y The ending y value in the image.
             */
            private get_hex_val(x: number, start_y: number, stop_y: number): number {
                // Number.toString(16) does not work in Arcade
                // This only works with numbers up to 15
                const numToHex = (num: number): string => {
                    if (num < 10) {
                        return num.toString();
                    } else {
                        const letters = ["a", "b", "c", "d", "e", "f"];
                        return letters[num - 10];
                    }
                }

                let hex_str: string = "";
                for (let y = start_y; y <= stop_y; y++) {
                    const px = this._img_ref.getPixel(x + 2, y);
                    hex_str += numToHex(px);
                }

                return parseInt(hex_str.length > 0 ? hex_str : "0", 16);
            }

            /**
             * Gets the duration at the specified X index.
             * 
             * @param x The x index, starting from 0.
             * @return The duration, in milliseconds.
             */
            public get_duration(x: number): number {
                return this.get_hex_val(x, this._duration_start_y, this._duration_stop_y);
            }

            /**
             * Gets the velocity at the specified X index.
             * 
             * @param x The x index, starting from 0.
             * @return The velocity.
             */
            public get_velocity(x: number): number {
                return this.get_hex_val(x, this._velocity_start_y, this._velocity_stop_y);
            }

            /**
             * Gets the notes at the specified X index.
             * 
             * @param x The x index, starting from 0.
             * @param A list of note indicies that are pressed.
             */
            public get_notes(x: number): number[] {
                const notes: number[] = [];

                let fake_y: number = 0;
                for (let y = this._note_start_y; y <= this._note_stop_y; y++) {
                    if (this._img_ref.getPixel(x + 2, y) != 0) {
                        notes.push(fake_y);
                    }
                    fake_y++;
                }

                return notes;
            }
        }

        export class ArcadeMIDIImageParser {
            private _stop: boolean;
            private _img_queue: Image[];
            private _frame_queue: ArcadeMIDIImageFrame[];

            public constructor() {
                this._stop = false;
                this._img_queue = [];
                this._frame_queue = [];
            }

            /**
             * Gets the image queue. 
             * 
             * @return A list of images.
             */
            get queue(): Image[] {
                return this._img_queue;
            }

            /**
             * Sets the image queue. 
             * Note: This will parse all the images to recompute neccessary information, and may take a long time.
             * 
             * @param new_queue The new list of images.
             */
            set queue(new_queue: Image[]) {
                this._img_queue = new_queue;
                this.recompute_frames(DEBUG_PARSING);
            }

            /**
             * Gets the frames, that you can pass to a ArcadeMIDIImageFramePlayer.
             * 
             * @return A list of frames, can be 0 length.
             */
            get frames(): ArcadeMIDI.ArcadeMIDIImageParser.ArcadeMIDIImageFrame[] {
                return this._frame_queue;
            }

            /**
             * Recomputes the frames from the images. 
             * Note: This will parse all the images to recompute neccessary information, and may take a long time.
             * 
             * @param debug Whether to log what we found or not.
             */
            private recompute_frames(debug: boolean = false): void {
                this._frame_queue = [];

                const log = (s: string) => {
                    if (debug) {
                        console.log(s);
                    }
                };

                for (const img of this._img_queue) {
                    let this_frame_start: number = 0;

                    for (let y = 0; y < img.height; y++) {
                        const prev_px = img.getPixel(0, y - 1);
                        const curr_px = img.getPixel(0, y);
                        const next_px = img.getPixel(0, y + 1);

                        if (prev_px != curr_px) {  // Start of new frame
                            this_frame_start = y;
                            log(`Found start of new frame at Y: ${y} (color: ${curr_px})`);
                        } else if (next_px != curr_px) {  // End of this frame
                            switch (curr_px) {
                                case (1): {  // White
                                    log(`Found note frame ending at Y: ${y} (color: ${curr_px})`);
                                    this._frame_queue.push(new ArcadeMIDIImageFrame(img, this_frame_start, y));
                                    break;
                                }
                                default: {
                                    log(`Found unknown frame ending at Y: ${y} (color: ${curr_px})`);
                                    break;
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    export namespace ArcadeMIDIImageFramePlayer {
        export class ArcadeMIDIImageFramePlayer {
            private _driver: ArcadeMIDI.ArcadeMIDIInternals.ArcadeMIDIInstructions;

            public constructor() {
                this._driver = new ArcadeMIDI.ArcadeMIDIInternals.ArcadeMIDIInstructions();
            }

            public play(frame: ArcadeMIDI.ArcadeMIDIImageParser.ArcadeMIDIImageFrame) {
                const log = (s: string) => {
                    if (DEBUG_PLAYING) {
                        console.log(s);
                    }
                };

                for (let x = 0; x < frame.frame_length; x++) {
                    const frame_time: number = frame.get_duration(x);
                    const frame_velocity: number = frame.get_velocity(x);
                    const frame_notes: number[] = frame.get_notes(x);

                    log(`Playing ${frame_notes.length} notes for ${frame_time} ms at ${frame_velocity} velocity`);
                    for (const note of frame_notes) {
                        this._driver.note_on(note, frame_velocity, 0, false);
                    }
                    this._driver.play_now(frame_time);
                    pause(frame_time);
                }
            }
        }

        export class ArcadeMIDIMultiImageFramePlayer {
            _frames: ArcadeMIDI.ArcadeMIDIImageParser.ArcadeMIDIImageFrame[];
            _driver: ArcadeMIDI.ArcadeMIDIImageFramePlayer.ArcadeMIDIImageFramePlayer;

            public constructor() {
                this._frames = [];
                this._driver = new ArcadeMIDI.ArcadeMIDIImageFramePlayer.ArcadeMIDIImageFramePlayer();
            }

            /**
             * Gets the image frames.
             * 
             * @return A list of frames.
             */
            get frames(): ArcadeMIDI.ArcadeMIDIImageParser.ArcadeMIDIImageFrame[] {
                return this._frames;
            }

            /**
             * Sets the image frames, and stops playing if we are.
             * 
             * @param new_frames A list of frames.
             */
            set frames(new_frames: ArcadeMIDI.ArcadeMIDIImageParser.ArcadeMIDIImageFrame[]) {
                this._frames = new_frames;
            }

            /**
             * Starts playing the music.
             */
            play(): void {
                for (const frame of this._frames) {
                    this._driver.play(frame);
                }
            }
        }
    }
}

const parser = new ArcadeMIDI.ArcadeMIDIImageParser.ArcadeMIDIImageParser();
parser.queue = {IMAGE_LIST};

const player = new ArcadeMIDI.ArcadeMIDIImageFramePlayer.ArcadeMIDIMultiImageFramePlayer();
player.frames = parser.frames;
player.play();

"""


def format_hex(num: int, min_len: int = 0) -> str:
    raw_hex = hex(num)[2:]
    return ("0" * (min_len - len(raw_hex))) + raw_hex


def format_col(time: int, velocity: int, notes: list[int]) -> str:
    """
    Formats a column.

    :param time: The time, in milliseconds.
    :param velocity: Velocity.
    :param notes: A list of MIDI note to press.
    :return: A string.
    """
    col = format_hex(time, 8)
    col += format_hex(velocity, 2)
    note_list = ["0"] * (88 + 21)
    for note in notes:
        note_list[note] = "f" if "#" in note_num_to_name(note - 21) else "1"
    col += "".join(note_list)
    col += "0"
    return col


image = []
width_count = 0

for msg in msgs:
    if msg.type == "note_on":
        logger.debug(f"Note message: {msg}")

        if width_count == 0:
            image.append(("1" * (8 + 2 + (88 + 21))) + "0")
            image.append(("3" * 8) + ("2" * 2) + ("1" * (88 + 21)) + "0")
            width_count = 2

        image.append(format_col(round(msg.time * 1000), msg.velocity, [msg.note]))

        width_count += 1
        if width_count == 512:
            width_count = 0
    else:
        logger.debug(f"Meta message: {msg}")


def format_cols_to_img(cols: list[str], pre_pad: str = "",
                       start_at: int = 0) -> str:
    """
    Flips an array sideways and makes it a string or something like that.

    :param cols: A list of strs.
    :param pre_pad: A string of what you want to pre_pad each line with.
     Defaults to "".
    :param start_at: Start at some point along the strings.
    :return: A string.
    """
    grid = ""
    for y in range(len(cols[0])):
        grid += f"{pre_pad}    "
        for x in range(start_at, min(len(cols), start_at + 512)):
            grid += f"{cols[x][y]} "
        grid += "\n"
    return grid


images_code = ""

if not to_stdout:
    logger.info(f"Writing {ceil(len(image) / 4 / 512)} images")

for i in range(0, len(image), 512 * 4):
    images_code += "    img`\n"
    for j in range(i, i + (512 * 4), 512):
        images_code += format_cols_to_img(image, pre_pad="", start_at=j)
    images_code += "    `,\n"

code = code.replace("{IMAGE_LIST}",
                    f"[\n{images_code}]")

if to_stdout:
    print(code)
else:
    logger.info(f"Writing to {out_path}")
    out_path.write_text(code)
