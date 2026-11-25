# MIDI Lab 4.2 — Effects Advisor

A **non-destructive** add-on to the complete 4.1 system (v3 and v4 commands remain unchanged).

The new `effects42.py` analyzes an existing Type 1 MIDI, reads its tempo and note-bearing track names, classifies roles, and generates **per-track Logic-oriented effect chains** as editable JSON. No MIDI notes are changed. Plug-ins and audio routing still need to be set up manually inside Logic Pro.

## Usage

```bash
pip install -r requirements.txt
python effects42.py examples/late_train_home.mid --preset midnight_motorik
python effects42.py /path/to/song.mid --preset bossa_afterglow --output /path/to/song.effects.json
python effects42.py /path/to/song.mid --all-presets --output /path/to/all_presets.json
python -m unittest discover -s tests -p 'test_v42.py' -v
```

Presets: `bossa_afterglow`, `tape_bliss`, `rigid_machine`, `fracture_void`, `broadcast_ident`, `midnight_motorik`.

## Dotted eighth guitar recipe

A dotted eighth note lasts **three sixteenth notes**, i.e. **0.75 quarter notes**. At 112 BPM, delay time is **401.79 ms**. The rhythmic echo creates a secondary strumming-like pattern without writing extra notes into the MIDI. On Logic Stereo Delay: sync to 3/16, use 15–24% feedback, 13–23% wet (insert) or fully wet on an auxiliary return, high-pass repeats at ~280 Hz and low-pass at ~4.5 kHz. Start conservative; a full wet delay on every guitar part can overcrowd bossa comping.

## Notes

- Chains are **starting points**, not universal settings or saved stock Logic presets.
- Drum-kit MIDI uses channel 10 conventions; kit mapping depends on your chosen instrument.
- Real effect quality depends on the instrument's sound, playing register, and mix.
- MIDI exports remain Type 1 / 480 PPQ as supplied, and the advisor never inserts program changes, bank select, or any other MIDI event.
- The `effects42.py` advisor works with arbitrary existing MIDI files, not only MIDI Lab creations.
