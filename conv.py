#!/usr/bin/env python3
import numpy as np
import gen_synth
import wave
import struct
import math

def read_wav(filename):
    file = wave.open(filename)
    amplitudes = []
    for _ in range(file.getnframes()):
        data = struct.unpack("<1h", file.readframes(1))
        amplitudes.extend(data)

    # Normalize to -1, 1
    return np.multiply(amplitudes, 1/32768)

raw = read_wav("Afar.wav")
# raw = raw[:len(raw)//8]
# response = np.array([ math.exp(-t/10000) for t in range(int(2*44100)) ])
# response /= 0.01*sum(response)
response = read_wav("notes/Hall - Medium 1.wav")
response /= 10
# response /= sum(np.abs(response))
filtered = np.convolve(raw, response)

def Generator(a, b):
    n = 0

    def f(t):
        nonlocal n
        nonlocal a
        nonlocal b
        n += 1
        sa = a[n-1] if n-1 < len(a) else 0
        sb = b[n-1] if n-1 < len(b) else 0
        return sb * 10**-2 + sa * 10**-0.8

    return f

gen_synth.gen_wav("Afar-reverb.wav", Generator(raw, filtered), len(filtered)/44100)
