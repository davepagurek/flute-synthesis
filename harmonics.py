#!/usr/bin/env python3

from gen_synth import note, note_name, midi_from_hz

base = note("C3")

print("Harmonic | Frequency | Note")
print("---------|-----------|-----")
for i in range(1, 11):
    f = base * i
    print(f"{i} | {f:.4f} | {note_name(midi_from_hz(f))}")
