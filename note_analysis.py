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
peak_phases = []
for note, filename in notes:
    file = wave.open(f"notes/{filename}.wav")
    amplitudes = []
    for _ in range(file.getnframes()):
        data = struct.unpack("<1h", file.readframes(1))
        amplitudes.extend(data)

    # Take the middle two quarters of data, approximately steady state
    amplitudes = amplitudes[len(amplitudes)//4:-len(amplitudes)//4]

    # Normalize to -1, 1
    amplitudes = np.multiply(amplitudes, 1/32768)
    times = np.multiply(range(len(amplitudes)), file.getframerate())

    # FFT is symmetrical, take the first half
    fft = np.fft.fft(amplitudes)[0:len(amplitudes)//2]
    band_amplitudes = np.absolute(fft)
    phases = np.angle(fft, deg=True)
    frequencies = [y * file.getframerate() / len(amplitudes) for y in range(len(amplitudes) // 2)]

    peaks, _ = signal.find_peaks(band_amplitudes, height=5, threshold=10, distance=30)
    max_idx = max(peaks, key=lambda i: band_amplitudes[i])
    peaks = [ i for i in peaks if frequencies[i] / frequencies[max_idx] > 0.2 ]

    peak_ratios.extend([frequencies[i] / frequencies[max_idx] for i in peaks])
    peak_amplitudes.extend([band_amplitudes[i] / band_amplitudes[max_idx] for i in peaks])
    peak_phases.extend([phases[i] - phases[max_idx] for i in peaks])

    fig, ax = plt.subplots(2, 1)
    fig.suptitle(note)

    ax[0].plot(times, amplitudes)
    ax[0].set_xlabel("Time (s)")
    ax[0].set_ylabel("Amplitude (dB)")

    ax[1].plot(frequencies, band_amplitudes)
    ax[1].plot([frequencies[i] for i in peaks], [band_amplitudes[i] for i in peaks], "x")
    ax[1].set_xscale("log", basex=2)
    ax[1].set_xlabel("Frequency (Hz)")
    ax[1].set_ylabel("Frequency Domain Amplitude")

    fig.tight_layout(rect=[0, 0.03, 1, 0.95])

fig, ax = plt.subplots(1, 1, sharex=True)
fig.suptitle("Harmonics")

ax.set_ylabel("Amplitude")
ax.scatter(peak_ratios, peak_amplitudes)

# ax[1].set_ylabel("Phase (Degrees)")
# ax[1].scatter(peak_ratios, peak_phases, s=np.add(np.multiply(peak_amplitudes, 20), 3))

ax.set_xlabel("Harmonic Ratio to Fundamental Frequency")
fig.tight_layout(rect=[0, 0.03, 1, 0.95])

plt.show()
