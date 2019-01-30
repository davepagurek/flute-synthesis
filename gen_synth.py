#!/usr/bin/env python3

import wave
import math
import struct
import numpy as np
from noise import pnoise1
from functools import reduce

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
    offsets = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]
    whole_midi = int(midi)
    cents = round((midi - whole_midi) * 100)
    octave = 4 + math.floor((whole_midi - 69)/12)
    offset = (whole_midi - 69) % 12

    note_str = f"{offsets[offset]}{octave}"
    if cents != 0:
        note_str += f" and {cents} cents"

    return note_str

def note(note_str):
    octave = int(note_str[-1])
    offsets = {"Ab":-1,"A":0,"A#":1,"Bb":1,"B":2,"C":3,"C#":4,"Db":4,"D":5,"D#":6,"Eb":6,"E":7,"F":8,"F#":9,"Gb":9,"G":10,"G#":11}
    offset = offsets[note_str[:-1]]
    return hz_from_midi((octave - 4) * 12 + offset + 69)

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
    return mult(const(velocity), envelope(a, d, s, r, max(0, length - a - d - r)))

def flute(note, length):
    vol = amplitude(-10)
    magnitude = 0.2
    offset = 0.8
    vibrato = add(const(0.7), mult(sigmoid(-0.4, scale=30),  sine(5, const(0.6))))
    return add(
        mult(
            lowpass2((1/44100)/((1/44100) + (1/15000)), noise(amplitude(-15))),
            note_envelope(length, 1, (0.01, 0.1, 0.3, 0.07))
        ),
        add(
            mult(const(vol), harmonics(note, {
                1: mult(note_envelope(length, 1, (0.04, 0.1, 0.5, 0.07)), random_wobble(magnitude, offset)),
                1.5: mult(note_envelope(length, 0.5, (0.04, 0.08, 0.14, 0.07)), random_wobble(magnitude, offset))
            })),
            mult(
                harmonics(note, {
                    2: scale(0.4 * vol, random_wobble(magnitude, offset)),
                    2.5: scale(0.06 * vol, random_wobble(magnitude, offset)),
                    3: mult(scale(0.3 * vol, random_wobble(magnitude, offset)), vibrato),
                    4: mult(scale(0.05 * vol, random_wobble(magnitude, offset)), vibrato),
                    5: mult(scale(0.05 * vol, random_wobble(magnitude, offset)), vibrato),
                    6: mult(scale(0.015 * vol, random_wobble(magnitude, offset)), vibrato),
                    7: mult(scale(0.002 * vol, random_wobble(magnitude, offset)), vibrato),
                    8: mult(scale(0.01 * vol, random_wobble(magnitude, offset)), vibrato),
                }),
                note_envelope(length, 1, (0.1, 0.1, 0.65, 0.07))
            )
        )
    )

if __name__ == "__main__":
    gen_wav("output.wav", flute(note("G4"), 1.2), 1.2)
