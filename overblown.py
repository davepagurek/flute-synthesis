#!/usr/bin/env python3
import numpy as np
from scipy import signal
import wave
import math
import struct
import matplotlib.pyplot as plt
from gen_synth import note_name

file = wave.open("notes/scale.wav")
wave_data = []
for _ in range(file.getnframes()):
    data = struct.unpack("<1h", file.readframes(1))
    wave_data.extend(data)

ratios = []
notes = []
names = []
amps = []
colors = []

overblown_x = []
overblown_y = []
normal_x = []
normal_y = []

for note, start_time in enumerate(range(4, 74, 2)):
    name = note_name(60 + note)
    name = name.replace("#", "^\sharp")
    names.append(f"${name[:-1]}_{name[-1]}$")

    # Get one note
    amplitudes = wave_data[start_time*44100:(start_time+2)*44100]

    # Take the middle four sixths of data, approximately steady state
    amplitudes = amplitudes[len(amplitudes)//6:-len(amplitudes)//6]

    # Normalize to -1, 1
    amplitudes = np.multiply(amplitudes, 1/32768)

    # FFT is symmetrical, take the first half
    fft = np.fft.fft(amplitudes)[0:len(amplitudes)//2]
    band_amplitudes = np.absolute(fft)
    frequencies = [y * file.getframerate() / len(amplitudes) for y in range(len(amplitudes) // 2)]

    peaks, _ = signal.find_peaks(band_amplitudes, height=5, threshold=2, distance=15)
    max_idx = max(peaks, key=lambda i: band_amplitudes[i])

    ratio = lambda i: frequencies[i] / frequencies[max_idx]

    peaks = [ i for i in peaks if ratio(i) < 7 and ratio(i) > 0.8 ]

    peak_amplitudes = [ band_amplitudes[i] / band_amplitudes[max_idx] for i in peaks ]

    # Round to nearest 0.5
    peak_ratios = [ (2*ratio(i))/2 for i in peaks ]

    overblown = any(round(ratio * 6) % 6 == 3 for ratio in peak_ratios)
    color = "#FAA81B" if overblown else "#1932BF"

    if overblown:
        overblown_x.extend(peak_ratios)
        overblown_y.extend(peak_amplitudes)
    else:
        normal_x.extend(peak_ratios)
        normal_y.extend(peak_amplitudes)

    ratios.extend(peak_ratios)
    amps.extend([ 1 - (x - 1)**4 for x in peak_amplitudes])
    notes.extend([ note for _ in peak_ratios ])
    colors.extend([ color for _ in peak_ratios ])

plt.scatter(notes, ratios, s=np.add(np.multiply(amps, 60), 5), color=colors)
plt.xticks(range(len(names)), names)
plt.title("Flute Note Harmonics")
plt.ylabel("Ratio to Highest Peak")
plt.xlabel("Note")

fig, ax = plt.subplots(1, 2, sharex=True, sharey=True)
ax[0].set_title("Normal")
ax[0].scatter(normal_x, normal_y)
ax[0].set_ylabel("Relative amplitude")
ax[0].set_xlabel("Harmonic")

ax[1].set_title("Overblown")
ax[1].scatter(overblown_x, overblown_y)
ax[1].set_xlabel("Harmonic")

plt.show()
