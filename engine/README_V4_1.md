# MIDI Lab 4.1 — Fracture / Bliss patch

Version 4.1 adds a **non-destructive, removable composition texture engine** on top of the complete original v4 and v3 sources. No additional dependency beyond `mido`.

## Quick start

From this folder:

```bash
python -m pip install -r requirements.txt
python midilab41.py cook --output examples/my_track.mid --bpm 116 --minutes 6 --key F# --mode minor --style hybrid --intensity 0.85 --drum-mode keep
```

Patch one of your own Type-1 / 480 PPQ MIDI files:

```bash
python midilab41.py patch --input my_song.mid --output my_song_fractured.mid --key F# --mode minor --style hybrid --drum-mode keep
```

Switch to a complex rhythm foundation:

```bash
python midilab41.py cook --output odd_clockwork.mid --bpm 128 --minutes 4 --style fracture --drum-mode replace --drum-complexity 1
```

## Modes

- `--style minimal` almost no new texture
- `--style bliss` sparse upper plucks and chord stabs over the original song
- `--style fracture` dense angular synth textures, altered harmony, displaced percussion
- `--style hybrid` low density → warm → fractured → integrated → sparse across five broad phases

Other controls: `--intensity 0..1`; `--drum-complexity 0..1`; `--seed`; `--drum-mode keep|replace|off`.

**Drum modes:** `keep` preserves the original v4 `Loop Drums` track bit-for-bit and adds optional separate Industrial Percussion on top. `replace` removes the original v4/v3 drum track and substitutes independent 4/4 kick-snare with 7/8 hats and 5/8 secondary percussion; `off` leaves original drums alone but suppresses industrial percussion overlays. Complex beat patterns are polymetric overlays **within a fixed 4/4 song grid**, not changing global time signatures. They're MIDI-ready for swapping drum kits and effects in Logic.

## What exactly is generated

The additional instrument roles, each independently removable in Logic, are:

1. Fracture Drums (only on replacement mode)
2. Bent Chord Stabs
3. Detuned Pluck Fragments
4. Industrial Percussion
5. Chromatic Counterline
6. Altered Harmony (extended minor-major ninth / chromatic-mediant / altered suspended harmonic vocabulary)

Tracks carry raw note-on / note-off MIDI events. No rendered effects, plugins, presets, parameter automation, audio, or pitch-bend envelopes are embedded. A `.texture_recipe.json` recommends Logic sound design per track. Instrument sounds are chosen in Logic.

## Compatibility and assurances

- All preexisting `midilab3.py` and `midilab4.py` commands and files remain unmodified.
- Source note events for immutable v4 pulse are compared verbatim to the patched MIDI; original drums likewise in `keep` mode.
- Type 1, 480 PPQ, no Program Change or Bank Select, no hanging or unpaired notes, zero same-note overlaps in exported MIDI (checked by `analyze3.py`).
- Deterministic seed; rerunning patch with the same settings produces byte-identical MIDI.
- `.audit.json` and `.texture_recipe.json` accompany each patched MIDI.
- Applying the same patch twice does not stack the same overlay tracks.

## Suggested audition order

1. `while_the_lights_bliss.mid` — your original 116 BPM, six-minute track with very light extra ornamentation.
2. `while_the_lights_fracture.mid` — *exact same base track*, dramatically complexified through the middle while keeping the pulse and drums identical.
3. `fractured_clockwork_128.mid` — 128 BPM, four-minute freshly composed complex rhythmic track with the replacement 7/8 and 5/8 percussion cycles.

## Testing

```bash
python -m unittest discover -s tests -p 'test_v*.py' -v
```

This is a rule-based **original** composition engine influenced by experimental synth-rock ideas rather than an imitation/transcription of any particular recording. Audition with your Logic instruments; the technical audit cannot assess musical taste.
