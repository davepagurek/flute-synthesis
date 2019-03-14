#!/usr/bin/env python3

import re
from gen_synth import note, note_name, midi_from_hz

base = note("C4")

print("Harmonic | Frequency | Note")
print("---------|-----------|-----")
for i in range(1, 11):
    f = base * i
    name = note_name(midi_from_hz(f))
    name = re.sub(r"([A-Z#]+)(\d)", r"$\1_\2$", name)
    name = name.replace("#", "^\\sharp")
    print(f"{i} & {f:.4f} & {name} \\\\")
