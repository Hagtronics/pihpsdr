"""
SDR9000 MIDI Controller

    Steve Hageman, July 2025

    # Modification to add +/- RIT to Tune Buttons Linked to Zoom Press

    Adafruit CircuitPython 9.2.8 on 2025-05-28; Raspberry Pi Pico with rp2040
"""

import board
import asyncio
import countio
import rotaryio
import keypad
import adafruit_midi
import usb_midi

import digitalio

# Midi control for buttons
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff

# Midi control for encoders
from adafruit_midi.control_change import ControlChange


# ==== Data structures ========================================================

# For the Midi command(s)
class MidiCommand():
    def __init__(self):
        self.command_ready = False
        self.type = "CC"            # "CC" or "NOTE"
        self.control_number = 0     # CC or NOTE Command Number
        self.value = 0              # Not used for "NOTE"

# Encoders change function, track with this
class EncoderFunctions():
    def __init__(self):
        self.function = []
        self.function.append("ZOOM")  # Zoom or RIT
        self.function.append("AF")  # AF or SQL
        self.function.append("RF")  # RF or AGC
        self.function.append("PAN_L")  # PAN_L or PAN_H


# Used to determine the Main Tuning Encoder rate of change
class TuningRate():
    def __init__(self):
        self.rate = 0


# ===== Helper Functions ======================================================

# Clamps encoder value to 0 - 127 range
def limit_encoder_range(input_value):
    return min(max(input_value, 0), 127)


# ===== Tasks =================================================================

# Sends MIDI command
async def send_midi_command(midi_cmd):
    # Setup
    midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0)

    while True:
        # Check if midi command and send
        if midi_cmd.command_ready == True:

            # Check message type
            if midi_cmd.type is "CC":
                # midi.send(ControlChange(7, af_value))
                midi.send(ControlChange(midi_cmd.control_number, midi_cmd.value))
                midi_cmd.command_ready = False

            elif midi_cmd.type is "NOTE":
                midi.send(NoteOn(midi_cmd.control_number, 127))
                # time.sleep(0.01)
                midi.send(NoteOff(midi_cmd.control_number, 0))
                midi_cmd.command_ready = False

        await asyncio.sleep(0)


# Reads the Tune Step buttons
async def tune_buttons(midi_cmd, encoder_functions):

    # Setup
    BUTTON_PINS = (
    board.GP6,  # Tune Step +
    board.GP7,  # Tune Step -
    )

    b = keypad.Keys(BUTTON_PINS,value_when_pressed=False, pull=True)

    while True:

        # Read tune buttons, check state change, form MIDI command
        event = b.events.get()

        if event:
            if event.released:
                if encoder_functions.function[0] == 'ZOOM':
                    # print(f'Button={event.key_number}')
                    # Tune +
                    if event.key_number == 0:
                        midi_cmd.type = "NOTE"
                        midi_cmd.control_number = 1
                        midi_cmd.command_ready = True

                    # Tune -
                    elif event.key_number == 1:
                        midi_cmd.type = "NOTE"
                        midi_cmd.control_number = 2
                        midi_cmd.command_ready = True

                elif encoder_functions.function[0] == 'RIT':
                    # print(f'Button={event.key_number}')
                    # RIT +
                    if event.key_number == 0:
                        midi_cmd.type = "NOTE"
                        midi_cmd.control_number = 20
                        midi_cmd.command_ready = True

                    # RIT -
                    elif event.key_number == 1:
                        midi_cmd.type = "NOTE"
                        midi_cmd.control_number = 21
                        midi_cmd.command_ready = True

        await asyncio.sleep(0)


# Encoder buttons
async def encoder_buttons(enc_functions):

    # Setup
    ENCODER_BUTTONS = (
    board.GP0,  # Switch on encoder 0 = ZOOM / RIT
    board.GP3,  # Switch on Encoder 1 = AF / SQL
    board.GP10, # Switch on Encoder 2 = RF / AGC
    board.GP13, # Switch on Encoder 3 = PAN L / PAN H
    )
    encoder_buttons = keypad.Keys(ENCODER_BUTTONS,value_when_pressed=False, pull=True)

    while True:
        event = encoder_buttons.events.get()

        if event and event.released:

        # Encoder 0 - ZOOM / RIT
            if event.key_number == 0:
                if enc_functions.function[0] == "ZOOM":
                    enc_functions.function[0] = "RIT"
                else:
                    enc_functions.function[0] = "ZOOM"


        # Encoder 1 - AF / AGC
            elif event.key_number == 1:
                if enc_functions.function[1] == "AF":
                    enc_functions.function[1] = "SQL"
                else:
                    enc_functions.function[1] = "AF"

            elif event.key_number == 2:
                if enc_functions.function[2] == "RF":
                    enc_functions.function[2] = "AGC"
                else:
                    enc_functions.function[2] = "RF"

            elif event.key_number == 3:
                if enc_functions.function[3] == "PAN_L":
                    enc_functions.function[3] = "PAN_H"
                else:
                    enc_functions.function[3] = "PAN_L"

        await asyncio.sleep(0)


# Process encoder 0 = Zoom
async def encoder_0(midi_cmd, encoder_functions):

    # Setup
    z_value = 0
    sensitivity = 10 # was 4

    encoder = rotaryio.IncrementalEncoder(board.GP1, board.GP2, divisor=4)

    last_position = 0
    while True:
        current_position = encoder.position
        position_change = current_position - last_position
        last_position = current_position

        if position_change != 0:

            if position_change > 0:
                z_value = limit_encoder_range(z_value + sensitivity)
                midi_cmd.type = "CC"
                midi_cmd.control_number = 9
                midi_cmd.value = z_value
                midi_cmd.command_ready = True

            elif position_change < 0:
                z_value = limit_encoder_range(z_value - sensitivity)
                midi_cmd.type = "CC"
                midi_cmd.control_number = 9
                midi_cmd.value = z_value
                midi_cmd.command_ready = True

        await asyncio.sleep(0)


# Process encoder 1 = AF/SQL
async def encoder_1(midi_cmd, encoder_functions):

    # Setup
    af_value = 0
    sql_value = 0
    sensitivity = 5

    encoder = rotaryio.IncrementalEncoder(board.GP4, board.GP5, divisor=4)

    last_position = 0
    while True:
        current_position = encoder.position
        position_change = current_position - last_position
        last_position = current_position

        if position_change != 0:

            if encoder_functions.function[1] == "AF":
                if position_change > 0:
                    af_value = limit_encoder_range(af_value + sensitivity)
                    midi_cmd.type = "CC"
                    midi_cmd.control_number = 10
                    midi_cmd.value = af_value
                    midi_cmd.command_ready = True

                elif position_change < 0:
                    af_value = limit_encoder_range(af_value - sensitivity)
                    midi_cmd.type = "CC"
                    midi_cmd.control_number = 10
                    midi_cmd.value = af_value
                    midi_cmd.command_ready = True

            elif encoder_functions.function[1] == "SQL":
                if position_change > 0:
                    sql_value = limit_encoder_range(sql_value + sensitivity)
                    midi_cmd.type = "CC"
                    midi_cmd.control_number = 11
                    midi_cmd.value = sql_value
                    midi_cmd.command_ready = True

                elif position_change < 0:
                    sql_value = limit_encoder_range(sql_value - sensitivity)
                    midi_cmd.type = "CC"
                    midi_cmd.control_number = 11
                    midi_cmd.value = sql_value
                    midi_cmd.command_ready = True

        await asyncio.sleep(0)


# Process encoder 2 = RF / AGC
async def encoder_2(midi_cmd, encoder_functions):

    # Setup
    rf_value = 0
    agc_value = 0
    sensitivity = 4

    encoder = rotaryio.IncrementalEncoder(board.GP11, board.GP12, divisor=4)

    last_position = 0
    while True:
        current_position = encoder.position
        position_change = current_position - last_position
        last_position = current_position

        if position_change != 0:

            if encoder_functions.function[2] == "RF":
                if position_change > 0:
                    rf_value = limit_encoder_range(rf_value + sensitivity)
                    midi_cmd.type = "CC"
                    midi_cmd.control_number = 12
                    midi_cmd.value = rf_value
                    midi_cmd.command_ready = True

                elif position_change < 0:
                    rf_value = limit_encoder_range(rf_value - sensitivity)
                    midi_cmd.type = "CC"
                    midi_cmd.control_number = 12
                    midi_cmd.value = rf_value
                    midi_cmd.command_ready = True

            elif encoder_functions.function[2] == "AGC":
                if position_change > 0:
                    agc_value = limit_encoder_range(agc_value + sensitivity)
                    midi_cmd.type = "CC"
                    midi_cmd.control_number = 13
                    midi_cmd.value = agc_value
                    midi_cmd.command_ready = True

                elif position_change < 0:
                    agc_value = limit_encoder_range(agc_value - sensitivity)
                    midi_cmd.type = "CC"
                    midi_cmd.control_number = 13
                    midi_cmd.value = agc_value
                    midi_cmd.command_ready = True

        await asyncio.sleep(0)


# Process encoder 3 = Pan H / L
async def encoder_3(midi_cmd, encoder_functions):

    # Setup
    pan_h_value = 0
    pan_l_value = 0
    sensitivity = 4

    encoder = rotaryio.IncrementalEncoder(board.GP14, board.GP15, divisor=4)

    last_position = 0
    while True:
        current_position = encoder.position
        position_change = current_position - last_position
        last_position = current_position

        if position_change != 0:

            if encoder_functions.function[3] == "PAN_L":
                if position_change > 0:
                    pan_h_value = limit_encoder_range(pan_h_value + sensitivity)
                    midi_cmd.type = "CC"
                    midi_cmd.control_number = 14
                    midi_cmd.value = pan_h_value
                    midi_cmd.command_ready = True

                elif position_change < 0:
                    pan_h_value = limit_encoder_range(pan_h_value - sensitivity)
                    midi_cmd.type = "CC"
                    midi_cmd.control_number = 14
                    midi_cmd.value = pan_h_value
                    midi_cmd.command_ready = True

            elif encoder_functions.function[3] == "PAN_H":
                if position_change > 0:
                    pan_l_value = limit_encoder_range(pan_l_value + sensitivity)
                    midi_cmd.type = "CC"
                    midi_cmd.control_number = 15
                    midi_cmd.value = pan_l_value
                    midi_cmd.command_ready = True

                elif position_change < 0:
                    pan_l_value = limit_encoder_range(pan_l_value - sensitivity)
                    midi_cmd.type = "CC"
                    midi_cmd.control_number = 15
                    midi_cmd.value = pan_l_value
                    midi_cmd.command_ready = True

        await asyncio.sleep(0)


# Looks at the tune rate of the Main Tuning Encoder
async def tune_rate(rate):

    # Setup
    pin_counter = countio.Counter(board.GP27, edge=countio.Edge.RISE)

    # Calculate rate
    while True:
        count = pin_counter.count
        pin_counter.reset()

        if count > 8:
            rate.value = 20
        elif count > 4:
            rate.value = 10
        else:
            rate.value = 0

        await asyncio.sleep(0.05)


# Reads the Main Tuning Encoder and using the rate at which it is bring tuned
async def tune_encoder(midi_cmd, rate):

    # TODO Debug code - remove
    led = digitalio.DigitalInOut(board.GP16)
    led.direction = digitalio.Direction.OUTPUT

    # Setup
    tuning = rotaryio.IncrementalEncoder(board.GP8, board.GP9, divisor=4)

    last_position = 0
    while True:
        # Read encoders, check state change, form MIDI command
        current_position = tuning.position
        position_change = current_position - last_position

        if position_change > 0:
            midi_cmd.type = "CC"
            midi_cmd.control_number = 1
            midi_cmd.value = 65 + rate.value
            midi_cmd.command_ready = True

        if position_change < 0:
            midi_cmd.type = "CC"
            midi_cmd.control_number = 1
            midi_cmd.value = 63 - rate.value
            midi_cmd.command_ready = True

        last_position = current_position

        # TODO Debug code - remove
        led.value = not led.value

        await asyncio.sleep(0)


# ===== Main ==================================================================

async def main():

    print('running.....')

    # Setup
    tuning_rate = TuningRate()
    encoder_functions = EncoderFunctions()
    midi_command = MidiCommand()

    # Make tasks objects
    tune_buttons_task = asyncio.create_task(tune_buttons(midi_command, encoder_functions))
    encoder_buttons_task = asyncio.create_task(encoder_buttons(encoder_functions))
    encoder_0_task = asyncio.create_task(encoder_0(midi_command, encoder_functions))
    encoder_1_task = asyncio.create_task(encoder_1(midi_command, encoder_functions))
    encoder_2_task = asyncio.create_task(encoder_2(midi_command, encoder_functions))
    encoder_3_task = asyncio.create_task(encoder_3(midi_command, encoder_functions))

    tune_rate_task = asyncio.create_task(tune_rate(tuning_rate))
    tune_enc_task = asyncio.create_task(tune_encoder(midi_command, tuning_rate))
    send_midi_task = asyncio.create_task(send_midi_command(midi_command))


    # Gather and run tasks - these run in endless loops never to return
    await asyncio.gather(tune_buttons_task,
                         encoder_buttons_task,
                         encoder_0_task,
                         encoder_1_task,
                         encoder_2_task,
                         encoder_3_task,
                         tune_rate_task,
                         tune_enc_task,
                         send_midi_task)

    # Main never gets here - unless something went very, very wrong!

# Program start point
asyncio.run(main())

# ----- Fini -----
