#!/usr/bin/env python3

import wave
import math
import struct
import numpy as np
from noise import pnoise1
from functools import reduce
import mido

# Generate a mono WAV file, with fs (sample rate) 44100 Hz and 16 bps (bits per sample)

def gen_wav(
        filename,
        generator,
        time,
        nchannels=1,
        sampwidth=2,
        fs=44100):
    output_file = wave.open(filename, 'w')
    output_file.setnchannels(nchannels)
    output_file.setsampwidth(sampwidth)
    output_file.setframerate(fs)
    output_file.setcomptype("NONE", "not compressed")

    total_frames = int(time * fs)
    output_file.setnframes(total_frames)

    for frame in range(total_frames):
        sample = generator(frame / fs)
        output_file.writeframes(struct.pack('h', int(np.clip(sample, -1, 1) * 32767)))

def add(generator_a, generator_b):
    return lambda t: generator_a(t) + generator_b(t)

def sub(generator_a, generator_b):
    return lambda t: generator_a(t) - generator_b(t)

def mult(generator_a, generator_b):
    return lambda t: generator_a(t) * generator_b(t)

def sine(frequency, amplitude, phase=0):
    return lambda t: amplitude(t) * math.sin(phase + t * 2 * math.pi * frequency)

def hz_from_midi(m):
    return 440 * math.pow(2, (m - 69)/12)

def midi_from_hz(hz):
    return math.log2(hz / 440) * 12 + 69

def amplitude(db):
    return math.pow(10, db/20)

def note_name(midi):
    offsets = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    whole_midi = int(midi)
    cents = round((midi - whole_midi) * 100)
    octave = 4 + math.floor((whole_midi - 60)/12)
    offset = (whole_midi - 60) % 12

    note_str = f"{offsets[offset]}{octave}"
    if cents != 0:
        note_str += f" and {cents} cents"

    return note_str

def note(note_str):
    octave = int(note_str[-1])
    offsets = {"Ab":8,"A":9,"A#":10,"Bb":10,"B":11,"C":0,"C#":1,"Db":1,"D":2,"D#":3,"Eb":3,"E":4,"F":5,"F#":6,"Gb":6,"G":7,"G#":8}
    offset = offsets[note_str[:-1]]
    return hz_from_midi((octave - 4) * 12 + offset + 60)

def harmonics(fundamental, amplitudes):
    oscillators = [ sine(fundamental * ratio, amplitude) for ratio, amplitude in amplitudes.items() ]
    return reduce(lambda a, b: add(a, b), oscillators)

def noise(amplitude):
    return lambda _: np.random.uniform(-1, 1) * amplitude

def random_wobble(scale=1, offset=0):
    t_offset = np.random.normal() * 20
    return lambda t: scale * pnoise1((t + t_offset)*10, 2) + offset

def scale(factor, fn):
    return lambda t: factor * fn(t)

def const(n):
    return lambda _: n

def sigmoid(offset, scale=1):
    return lambda t: 1/(math.exp(-scale * (t + offset)) + 1)

def lowpass(a, fn):
    last = 0
    
    def lowpass_impl(t):
        nonlocal a
        nonlocal last
        last += a * (fn(t) - last)
        return last

    return lowpass_impl

def lowpass2(a, fn):
    last = [0, 0]
    
    def lowpass_impl(t):
        nonlocal a
        nonlocal last

        next_val = (a**2) * fn(t)
        next_val -= 2*(a - 1)*last[-1]
        next_val -= ((1-a)**2) * last[-2]

        last.append(next_val)
        last.pop(0)

        return next_val

    return lowpass_impl

def time_offset(fn, delay):
    return lambda t: fn(t - delay)

def scoped(t1, t2, fn):
    return lambda t: fn(t - t1) if t1 <= t and t < t2 else 0

def piecewise(fns):
    pieces = [ scoped(t1, t2, fn) for (t1, t2), fn in fns ]
    return reduce(lambda a, b: add(a, b), pieces)

def decay(A, tau):
    return lambda t: A * math.exp(-t / tau)

def attack(A, tau):
    return lambda t: A * (1 - math.exp(-t / tau))

def line(x1, y1, x2, y2):
    return lambda t: (y2 - y1)/(x2 - x1) * (t - x1) + y1

def envelope(a, d, s, r, s_time):
    return piecewise([
        ((0, a), line(0, 0, a, 1)),
        ((a, a+d), line(0, 1, d, s)),
        ((a+d, a+d+s_time), const(s)),
        ((a+d+s_time, a+d+s_time+r), line(0, s, r, 0))
    ])

def note_envelope(length, velocity, adsr):
    a, d, s, r = adsr
    s_length = length - a - d - r
    if s_length < 0:
        s_length = 0
        a_ratio = a / (a + d + r)
        d_ratio = d / (a + d + r)
        r_ratio = r / (a + d + r)
        a = a_ratio * length
        d = d_ratio * length
        r = r_ratio * length
    return mult(const(velocity), envelope(a, d, s, r, max(0, length - a - d - r)))

def flute(note, length, velocity):
    vol = amplitude(-10)
    magnitude = 0.2 * velocity
    offset = 0.8
    vibrato = add(const(0.7), mult(sigmoid(-0.4, scale=30),  sine(5, const(0.6))))

    def overblown(f):
        # ~D5 to ~D#7
        if f > 580 and f < 1300:
            return True

        # ~F#6
        if f > 1460:
            return True

        return False

    is_overblown = overblown(note)

    delay = 0.02 if is_overblown else 0
    attack_overblow = 1.8

    peaks = {
        1: (0, 0),
        1.5: (-math.inf, -1.75),
        2: (-0.25, -1),
        2.5: (-math.inf, -2.5),
        3: (-1, -1.75),
        4: (-1.25, -2),
        5: (-2, -2.5),
        6: (-2.25, -2.6),
        7: (-2.3, -2.7)
    }

    def get_vol(h):
        val = 10**peaks[h][1 if is_overblown else 0]
        if h % 2 == 1 and h > 1:
            val *= attack_overblow
        return val

    env_odd = note_envelope(length - delay, 1, (
        0.1 if is_overblown else 0.02,
        0.1,
        0.65,
        0.07
    ))
    env_even = note_envelope(length - delay, 1, (
        0.1 if is_overblown else 0.02,
        0.1,
        0.65 / attack_overblow,
        0.07
    ))
    return add(
        mult(
            lowpass2((1/44100)/((1/44100) + (1/15000)), noise(amplitude(-18))),
            note_envelope(length, 1 if is_overblown else 0.7, (0.01, 0.1, 0.3, 0.07))
        ),
        add(
            mult(const(vol), harmonics(note, {
                1: mult(note_envelope(length, get_vol(1), (0.02, 0.1, 0.5, 0.07)), random_wobble(magnitude, offset)),
                1.5: mult(note_envelope(length, get_vol(1.5), (0.02, 0.08, 0.14, 0.07)), random_wobble(magnitude, offset)),
                2.5: mult(note_envelope(length, get_vol(2.5), (0.02, 0.08, 0.14, 0.07)), random_wobble(magnitude, offset))
            })),
            time_offset(harmonics(note, {
                2: mult(env_even, scale(get_vol(2) * vol, random_wobble(magnitude, offset))),
                3: mult(env_odd, mult(scale(get_vol(3) * vol, random_wobble(magnitude, offset)), vibrato)),
                4: mult(env_even, mult(scale(get_vol(4) * vol, random_wobble(magnitude, offset)), vibrato)),
                5: mult(env_odd, mult(scale(get_vol(5) * vol, random_wobble(magnitude, offset)), vibrato)),
                6: mult(env_even, mult(scale(get_vol(6) * vol, random_wobble(magnitude, offset)), vibrato)),
                7: mult(env_odd, mult(scale(get_vol(7) * vol, random_wobble(magnitude, offset)), vibrato)),
            }), delay)
        )
    )

def synth_from_midi(f, channels, synth, extend=0):
    mid = mido.MidiFile(f)

    notes = []

    sounding_events = dict()
    for channel in channels:
        sounding_events[channel] = dict()
    time = 0

    for msg in mid:
        time += msg.time

        if msg.type == "note_on" and msg.velocity > 0 and msg.channel in channels:
            if msg.note in sounding_events[msg.channel]:
                print(msg)
                print(sounding_events)
                raise Exception("Duplicate note")
            note = {"note": hz_from_midi(msg.note), "start": time, "velocity": msg.velocity/100}
            sounding_events[msg.channel][msg.note] = note
            notes.append(note)
        elif (msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0)) and msg.channel in channels:
            note = sounding_events[msg.channel][msg.note]
            note["end"] = time+extend
            note["generator"] = synth(note["note"], note["end"] - note["start"], note["velocity"])
            sounding_events[msg.channel].pop(msg.note)

    for _, channel in sounding_events.items():
        for _, note in channel.items():
            note["end"] = time+extend
            note["generator"] = synth(note["note"], note["end"] - note["start"], note["velocity"])

    sounding = []

    # Assumes monotonic t
    def generator(t):
        nonlocal synth
        nonlocal notes
        nonlocal sounding

        while len(notes) > 0 and notes[0]["start"] <= t:
            sounding.append(notes.pop(0))

        sounding = [ n for n in sounding if n["end"] >= t ]

        total = 0
        for n in sounding:
            total += n["generator"](t - n["start"])

        return total

    return generator, time+extend

if __name__ == "__main__":
    generator, length = synth_from_midi("Afar.mid", set([0, 1]), flute, extend=0.02)
    gen_wav("Afar.wav", generator, length)
    # gen_wav("output.wav", flute(note("A4"), 2.5, 1), 2.5)
