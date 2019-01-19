#!/usr/bin/env python3

import numpy as np
from scipy import signal
import wave
import math
import struct
import matplotlib.pyplot as plt

comptype="NONE"
compname="not compressed"
nchannels=1
sampwidth=2

notes = [
    ("G", "g"),
    ("F", "f"),
    ("E$\\flat$", "e flat"),
    ("D", "d")
]

peak_ratios = []
peak_amplitudes = []
for note, filename in notes:
    file = wave.open(f"notes/{filename}.wav")
    amplitudes = []
    for _ in range(file.getnframes()):
        data = struct.unpack("<1h", file.readframes(1))
        amplitudes.extend(data)

    # Normalize to -1, 1
    amplitudes = np.multiply(amplitudes, 1/32768)
    times = np.multiply(range(len(amplitudes)), file.getframerate())

    # FFT is symmetrical, take the first half
    fft = np.fft.fft(amplitudes)[0:len(amplitudes)//2]
    band_amplitudes = np.abs(fft)
    frequencies = [y * file.getframerate() / len(amplitudes) for y in range(len(amplitudes) // 2)]

    peaks, _ = signal.find_peaks(band_amplitudes, height=50, threshold=20, distance=50)

    peak_ratios.extend([frequencies[i] / frequencies[peaks[0]] for i in peaks])
    peak_amplitudes.extend([band_amplitudes[i] / band_amplitudes[peaks[0]] for i in peaks])

    fig, ax = plt.subplots(2, 1)
    fig.suptitle(note)

    ax[0].plot(times, amplitudes)
    ax[0].set_xlabel("Time (s)")
    ax[0].set_ylabel("Amplitude")

    ax[1].plot(frequencies, band_amplitudes)
    ax[1].plot([frequencies[i] for i in peaks], [band_amplitudes[i] for i in peaks], "x")
    ax[1].set_xscale("log", basex=2)
    ax[1].set_xlabel("Frequency (Hz)")
    ax[1].set_ylabel("Amplitude")

    fig.tight_layout(rect=[0, 0.03, 1, 0.95])

fig, ax = plt.subplots(1, 1)
fig.suptitle("Harmonics")

ax.set_xlabel("Ratio to Fundamental Frequency")
ax.set_ylabel("Amplitude")
ax.scatter(peak_ratios, peak_amplitudes)

plt.show()
