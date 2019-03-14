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
    band_amplitudes = np.log10(np.absolute(fft) * 2 / len(amplitudes))
    frequencies = [y * file.getframerate() / len(amplitudes) for y in range(len(amplitudes) // 2)]

    peaks, _ = signal.find_peaks(band_amplitudes, height=-3.75, threshold=0.08, distance=41)
    # if note == 11:
        # plt.plot(frequencies, band_amplitudes)
        # plt.plot([frequencies[i] for i in peaks], [band_amplitudes[i] for i in peaks], "x")
        # plt.xscale("log", basex=2)
        # plt.show()
    max_idx = max(peaks, key=lambda i: band_amplitudes[i])
    max_idx = next(i for i in peaks if band_amplitudes[i] > -2)

    ratio = lambda i: frequencies[i] / frequencies[max_idx]

    peaks = [ i for i in peaks if ratio(i) < 7 and ratio(i) > 0.8 ]
    if frequencies[max_idx] > 274 and frequencies[max_idx] < 279:
        peaks = [ i for i in peaks if ratio(i) < 1.2 or ratio(i) > 1.8 ]

    peak_gains = [ band_amplitudes[i] - band_amplitudes[max_idx] for i in peaks ]

    peak_ratios = [ ratio(i) for i in peaks ]

    overblown = any(round(ratio * 9) % 9 in [3, 4, 5] for ratio in peak_ratios)
    color = "#FAA81B" if overblown else "#1932BF"

    if overblown:
        overblown_x.extend(peak_ratios)
        overblown_y.extend(peak_gains)
    else:
        normal_x.extend(peak_ratios)
        normal_y.extend(peak_gains)

    ratios.extend(peak_ratios)
    amps.extend([ 1 - (x/3)**2 for x in peak_gains])
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
ax[0].set_ylabel("Gain from Peak")
ax[0].set_xlabel("Harmonic")

ax[1].set_title("Overblown")
ax[1].scatter(overblown_x, overblown_y)
ax[1].set_xlabel("Harmonic")

plt.show()
