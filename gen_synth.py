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

    total_frames = time * fs
    output_file.setnframes(total_frames)

    for frame in range(total_frames):
        sample = generator(frame / fs)
        output_file.writeframes(struct.pack('h', int(np.clip(sample, -1, 1) * 32767)))

def add(generator_a, generator_b):
    return lambda t: generator_a(t) + generator_b(t)

def mult(generator_a, generator_b):
    return lambda t: generator_a(t) * generator_b(t)

def sine(frequency, amplitude):
    return lambda t: amplitude(t) * math.sin(t * 2 * math.pi * frequency)

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
    return lambda _: np.random.normal(0, 1) / 3 * amplitude

def random_wobble(scale=1, offset=0):
    t_offset = np.random.normal() * 20
    return lambda t: scale * pnoise1((t + t_offset)*10, 2) + offset

def scale(factor, fn):
    return lambda t: factor * fn(t)

def const(n):
    return lambda _: n

def lowpass(alpha, fn):
    last = 0
    
    def lowpass_impl(t):
        nonlocal alpha
        nonlocal last
        last += alpha * (fn(t) - last)
        return last

    return lowpass_impl

def flute(note):
    vol = amplitude(-10)
    magnitude = 0.4
    offset = 0.6
    vibrato = add(const(0.7), sine(5, const(0.3)))
    return add(
        lowpass(20000/44100, noise(amplitude(-35))),
        # noise(amplitude(-35)),
        harmonics(note, {
            1: scale(vol, random_wobble(magnitude, offset)),
            1.5: scale(0.07 * vol, random_wobble(magnitude, offset)),
            2: scale(0.4 * vol, random_wobble(magnitude, offset)),
            2.5: scale(0.06 * vol, random_wobble(magnitude, offset)),
            3: mult(scale(0.3 * vol, random_wobble(magnitude, offset)), vibrato),
            4: mult(scale(0.05 * vol, random_wobble(magnitude, offset)), vibrato),
            5: mult(scale(0.05 * vol, random_wobble(magnitude, offset)), vibrato),
            6: mult(scale(0.015 * vol, random_wobble(magnitude, offset)), vibrato),
            7: mult(scale(0.002 * vol, random_wobble(magnitude, offset)), vibrato),
            8: mult(scale(0.01 * vol, random_wobble(magnitude, offset)), vibrato),
        })
    )

if __name__ == "__main__":
    gen_wav("output.wav", flute(note("G4")), 1)
