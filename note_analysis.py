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


fig, ax = plt.subplots(2, 2, figsize=(12, 6), sharex=True, sharey=True)
for i, (note, filename) in enumerate(notes):
    file = wave.open(f"notes/{filename}.wav")
    amplitudes = []
    for _ in range(file.getnframes()):
        data = struct.unpack("<1h", file.readframes(1))
        amplitudes.extend(data)

    # Take the middle four sixths of data, approximately steady state
    amplitudes = amplitudes[len(amplitudes)//6:-len(amplitudes)//6]

    # Normalize to -1, 1
    amplitudes = np.multiply(amplitudes, 1/32768)
    times = np.multiply(range(len(amplitudes)), file.getframerate())

    # FFT is symmetrical, take the first half
    fft = np.fft.fft(amplitudes)[0:len(amplitudes)//2]
    band_amplitudes = np.log10(np.absolute(fft) * 2 / len(amplitudes))
    phases = np.angle(fft, deg=True)
    frequencies = [y * file.getframerate() / len(amplitudes) for y in range(len(amplitudes) // 2)]

    # peaks, _ = signal.find_peaks(band_amplitudes, height=0, threshold=0, distance=30)
    peaks, _ = signal.find_peaks(band_amplitudes, height=-3, distance=41)
    max_idx = next(i for i in peaks if band_amplitudes[i] > -2)
    # max_idx = next(i for i in peaks if band_amplitudes[i] > 1000)
    # max_idx = max(peaks, key=lambda i: band_amplitudes[i])
    peaks = [ i for i in peaks if frequencies[i] / frequencies[max_idx] > 0.3 ]

    peak_ratios.extend([frequencies[i] / frequencies[max_idx] for i in peaks])
    peak_amplitudes.extend([band_amplitudes[i] - band_amplitudes[max_idx] for i in peaks])
    peak_phases.extend([phases[i] - phases[max_idx] for i in peaks])

    a = ax.item(i)

    a.set_title(note)

    # ax[0].plot(times, amplitudes)
    # ax[0].set_xlabel("Time (s)")
    # ax[0].set_ylabel("Amplitude (dB)")

    a.plot(frequencies, band_amplitudes)
    a.plot([frequencies[i] for i in peaks], [band_amplitudes[i] for i in peaks], "x")
    a.set_xscale("log", basex=2)

    if i % 2 == 0:
        a.set_ylabel("Amplitude (dB)")
    if i > 1:
        a.set_xlabel("Frequency (Hz)")

fig.tight_layout(rect=[0, 0.03, 1, 0.95])

fig, ax = plt.subplots(1, 1, sharex=True, figsize=(7, 3))
fig.suptitle("Harmonics")

ax.set_ylabel("Gain from Peak (dB)")
ax.scatter(peak_ratios, peak_amplitudes)

# ax[1].set_ylabel("Phase (Degrees)")
# ax[1].scatter(peak_ratios, peak_phases, s=np.add(np.multiply(peak_amplitudes, 20), 3))

ax.set_xlabel("Harmonic Ratio to Fundamental Frequency")
fig.tight_layout(rect=[0, 0.03, 1, 0.95])

plt.show()
