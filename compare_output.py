#!/usr/bin/env python3

import numpy as np
from scipy import signal
import wave
import math
import struct
import matplotlib.pyplot as plt

from gen_synth import flute, note

comptype="NONE"
compname="not compressed"
nchannels=1
sampwidth=2

notes = [
    ("G4", "notes/g.wav"),
]

def read_wav(filename):
    file = wave.open(filename)
    amplitudes = []
    for _ in range(file.getnframes()):
        data = struct.unpack("<1h", file.readframes(1))
        amplitudes.extend(data)

    # Normalize to -1, 1
    return np.multiply(amplitudes, 1/32768)

for notename, filename in notes:
    real = read_wav(filename)
    
    generator = flute(note(notename))
    synth = np.array([ generator(t / 44100) for t in range(len(real)) ])

    fig, ax = plt.subplots(1, 2, sharex=True, sharey=True)
    for i, (title, sound) in enumerate([("Real", real), ("Synthesized", synth)]):
        freqs, times, Sx = signal.spectrogram(sound, fs=44100,
                nperseg=1024, noverlap=24,
                detrend=False, scaling='spectrum')

        # Colormap names: https://matplotlib.org/examples/color/colormaps_reference.html
        ax[i].pcolormesh(times, freqs / 1000, 10 * np.log10(Sx), cmap='plasma')
        if i == 0:
            ax[i].set_ylabel('Frequency (kHz)')
        ax[i].set_xlabel('Time (s)')
        ax[i].set_title(title)

    fig.tight_layout(rect=[0, 0.03, 1, 0.95])

plt.show()
