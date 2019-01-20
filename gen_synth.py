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

def sine(frequency, amplitude):
    return lambda t: amplitude(t) * math.sin(t * 2 * math.pi * frequency)

def hz_from_midi(m):
    return 440 * math.pow(2, (m - 69)/12)

def amplitude(db):
    return math.pow(10, db/20)

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

def flute(note):
    vol = amplitude(-10)
    magnitude = 0.4
    offset = 0.6
    return add(
        noise(amplitude(-35)),
        harmonics(note, {
            1: scale(vol, random_wobble(magnitude, offset)),
            1.5: scale(0.07 * vol, random_wobble(magnitude, offset)),
            2: scale(0.4 * vol, random_wobble(magnitude, offset)),
            2.5: scale(0.06 * vol, random_wobble(magnitude, offset)),
            3: scale(0.3 * vol, random_wobble(magnitude, offset)),
            4: scale(0.05 * vol, random_wobble(magnitude, offset)),
            5: scale(0.05 * vol, random_wobble(magnitude, offset)),
            6: scale(0.015 * vol, random_wobble(magnitude, offset)),
            7: scale(0.002 * vol, random_wobble(magnitude, offset)),
            8: scale(0.01 * vol, random_wobble(magnitude, offset)),
        })
    )

if __name__ == "__main__":
    gen_wav("output.wav", flute(note("G4")), 1)
