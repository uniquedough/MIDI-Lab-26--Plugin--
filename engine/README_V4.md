# MIDI Lab 4.0 — Emotional Architecture / Repetition / Performance

**A backwards-compatible v3 extension, not a learned neural composition model.** Requires Python 3.10+ and `mido` (`pip install -r requirements.txt`). Everything from MIDI Lab 3.0 is retained: its original engine and CLI (`midilab3.py`), harmony, genre engines, fretboard guitar tools, 27 taste profiles, manifests, MIDI analyzer, prior example MIDIs, feedback ledger and legacy implementation. `midilab4.py` adds a deliberately **loop-first** family of compositions optimized for emotionally evolving minimalism. To compose in the broader original v3 arrangement grammar, run `midilab3.py cook` unchanged.

## Run v4

```bash
python midilab4.py cook --key B --mode minor --bpm 94 --minutes 8 --repetition immutable --arc regret,numbness,recognition,acceptance,triumph --instrument-detail expressive --output examples/my_elegy.mid
python midilab4.py cook --key E --mode minor --bpm 120 --minutes 4 --repetition microevolution --profile no_technique_balearic --arc yearning,regret,recognition,acceptance,triumph --output examples/my_motion.mid
python midilab4.py cook --key Eb --mode dorian --bpm 136 --minutes 2.5 --repetition phase --profile pink_bedroom_2step --output examples/my_phase.mid
```

### 1. Emotional architecture
`--arc` accepts ordered comma-separated states (`regret`, `numbness`, `recognition`, `acceptance`, `triumph`, `yearning`, `unease`, `tenderness`). The engine maps states to chord-color changes over a pedal, note-range choices, selective phrase omissions, upper-register melodic emphasis, and expression dynamics. Emotional labels are compositional directives, not scientific measures of emotion.

### 2. Repetition intelligence
`--repetition immutable` retains a fixed pulse and drums while minimizing other moving parts. `microevolution` retains fixed pulse and drums, allowing sparse pluck omissions, bass comments and occasional guitar answers. `phase` uses a shifting five-phase pluck alignment and a three-bar companion-guitar cycle over the fixed grid. **The fixed two-bar rhythm and pulse are invariant in all three modes.** Their exact bytes are not identical (MIDI offsets encode events); their decoded note, tick, duration, velocity, and channel patterns match across cycles. `*.locks.json` documents the programmatically proven comparison.

### 3. Realistic performance
`--instrument-detail machine|natural|expressive` governs deterministic instrument-specific articulation and accents (bar strong beats, end-of-phrase relaxation, bass root emphasis, non-root damping, short guitar gates, longer sustained upper voices, micro-offsets). Invariant tracks are exempt. MIDI velocity/phrasing are only instructions: sound depends on the instrument patch; no Program Changes or Bank Select are inserted. Some subtleties of physical playing, MPE, tuning, and sample-layer articulation are not modeled.

### Safeguards
- Type 1, 480 PPQ, named tracks, patch-agnostic, no CC0/CC32 or Program Change.
- `*.manifest.json` records the section map, emotional arc and roles.
- `*.audit.json` includes existing v3 analyzer checks.
- `*.locks.json` certifies exact pattern identity for the two fixed tracks.
- MIDI note generation is deterministic with identical inputs and seeds.
- Durations round to a **complete two-bar cycle**, so final actual duration may differ slightly from the requested number of minutes. 94 BPM and 8 minutes = exactly 188 bars, 94 identical two-bar loops.

## Examples
- `examples/eight_minute_unmoving.mid` — 94 BPM / B minor / 8:00 / immutable loop / regret to triumph.
- `examples/late_train_home.mid` — 120 BPM / E minor / 4:00 / slow microevolution.
- `examples/blue_window_phase.mid` — 136 BPM / Eb Dorian / ~2:32 / interacting phase cycles.

## Quality and scope
This is a **working rule-based algorithm**, not an audio-generating program. The v4 loop-first renderer deliberately avoids conventional chorus/drop writing; it does not supersede v3 for general songs. The emotion stages are harmonic/density heuristics. Instrument performance is MIDI-instrument dependent, and timbral filter changes still need automation in Logic. The core pulse is a pitch-constant repetitive note; no sample-based audio effects are encoded. The current v4 drum pattern is intentionally fixed and generic for this specific mode, rather than selecting all eight v3 drum families.

Run all tests:

```bash
python -m unittest discover -s tests -v
```
