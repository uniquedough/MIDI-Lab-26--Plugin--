# MIDI Lab 3.0 — Musical Intelligence

A portable, working, **rule-based** multitrack MIDI composer, feedback log, performance processor, and structural MIDI analyzer. It extends the v2.4 profile library **without deleting previous tastes**.

**Important:** Downloading the ZIP does not automatically install a native ChatGPT skill. You can place `SKILL.md`, `style_profiles.json`, `taste_ledger.json` and `PROJECT_INSTRUCTIONS.txt` inside a ChatGPT Project, or run the Python composer locally. The command-line tool is the executable portion of the skill.

## What's genuinely new since v2.4

| Feature | Before | v3.0 |
|---|---|---|
| Tonics/scales | Mostly a fixed A-major family | All 12 tonics, major/minor/Dorian/Mixolydian |
| Harmonic variation | Several fixed chords and manual borrows | Four mood strategies, section progressions, modal borrowing and partial add9 colors |
| Voicings | Mostly octave-snapped | Enumerated four-voice arrangements minimizing motion and collisions |
| Drum families | General-purpose pattern | Eight purpose-built groove families and characteristic ghost/swing/fill logic |
| Guitar logic | MIDI notes in generic range | Standard-tuning fretted chord grip search and picked patterns |
| Instrument performance | v2.4 humanization postprocessor | Retained and integrated as an optional per-role performance pass |
| Analysis | Density and note ranges | Section activity, track velocity distribution, contours, groove-grid histograms, bass-kick overlap and comparison |
| Iteration | Same-seed variants | Preserved; new altered hook endings and explicit borrowed harmonic context |
| User taste | Local ledger | Retained; feedback CLI and approval-only parameter adjustments |

## Setup

```bash
python -m pip install mido
python midilab3.py profiles
```

No APIs or internet access required. Python 3.10+ recommended.

## Run the three recipes

### 1 — Human versus machine New Order palette

```bash
python midilab3.py cook --profile no_technique_balearic --harmony no_republic_afterglow --rhythm no_technique_balearic --bass no_technique_balearic --melody no_pcl_sunrise --arrangement no_technique_balearic --key F# --mode minor --bpm 124 --minutes 3.6 --seed 1989 --performance neworder --output examples/neon_afterglow_neworder.mid
```

### 2 — Soft UK garage / PinkPantheress-flavored brief

```bash
python midilab3.py cook --profile pink_bedroom_2step --harmony ukg_elegant_night --rhythm pink_bedroom_2step --bass pink_bedroom_2step --melody pink_bedroom_2step --arrangement pink_fancy_club --key Eb --mode dorian --bpm 136 --minutes 2.6 --seed 2036 --performance tight --output examples/velvet_corners_ukg.mid
```

### 3 — The Drums x Yo La Tengo minimal ballad

```bash
python midilab3.py cook --profile drums_solo_jonny --harmony yl_tender_nocturne --rhythm drums_solo_abysmal --bass drums_solo_jonny --melody drums_solo_jonny --arrangement yl_tender_nocturne --key D --mode major --drums ballad --bpm 76 --minutes 4 --seed 7624 --variant restrained --performance natural --output examples/windows_still_glowing_ballad.mid
```

## Explore variations and analysis

```bash
python midilab3.py cook --profile no_technique_balearic --key F# --mode minor --bpm 124 --minutes 3.6 --seed 1989 --variant strange --performance neworder --output examples/alternate.mid
python midilab3.py analyze --input examples/neon_afterglow_neworder.mid --manifest examples/neon_afterglow_neworder.manifest.json
python midilab3.py compare --a examples/neon_afterglow_neworder.mid --b examples/neon_afterglow_strange.mid
python midilab3.py feedback --track neon_afterglow --part melodic_bass --rating 5 --note 'Love the upper-register movement' --tags melodic,postpunk
# Only after deliberately approving a taste adjustment:
python midilab3.py approve-adjustment --parameter bass_motion --delta 1
```

## Outputs
- `.mid`: patch-independent multitrack MIDI with notes, tempo, key signature, meter, markers.
- `.manifest.json`: exact keys/roles, section form, selected chords and voicings, playable guitar frets, recorded motif operations, seed.
- `.audit.json`: MIDI technical validation plus measurable structural features.
- `.performance.json`: per-role velocity and gate treatment log when performance applied.

`logic_sound_roles.json` contains practical sound-assignment suggestions, not actual Logic preset files. MIDI cannot encode tape hiss, live feedback, effects chains, or a realistic recorded voice.

## Limitations / honest scope

This is a **musically structured algorithm**, not a trained model that can listen to songs or assess whether the final result is catchy. The pattern library still contains authored forms and rhythmic cells, although it is far more flexible than the fixed A-major generator. Chord symbols in the manifest approximate their actual pitch-class content. Fretboard shapes assume standard tuning and do not simulate finger physiology fully. Groove-specific realism is improved but not equivalent to a recorded drummer. Its `mood`, `key`, `mode`, `drums`, and `seed` inputs affect concrete note generation; artist profiles supply adjustable numerical behaviors and style guidance rather than copying songs.

The technical validator rejects forbidden MIDI metadata and unmatched/stuck notes. Passing validation is **not** equivalent to passing the subjective songwriting critique.

## Files
- `midilab3.py` — main CLI composer, taste feedback and variant behavior
- `harmony3.py` — transposition, progression, borrowed harmony and voicing search
- `rhythm3.py` — distinct drum patterns and mutation logic
- `fretboard3.py` — reachable guitar chord shapes / arpeggios
- `analyze3.py` — MIDI inspection and comparisons
- `performance.py` — inherited and retained instrument performance processor
- `style_profiles.json` — 27 original taste profiles and references
- `taste_ledger.json` — observed user preferences and explicit-only adjustment weights
- `logic_sound_roles.json` — patches and processing guidance
- `SKILL.md`, `PROJECT_INSTRUCTIONS.txt`, `PROMPT_RECIPES.md`, `QA_CHECKLIST.md` — workflow and composer specification
- `examples` — playable MIDIs plus audit and manifests
- `tests` — unittest suite and previously accepted MIDI benchmark examples
- `legacy` — original v2.4 engine (for compatibility)

## Quick QA

```bash
python -m unittest discover -s tests -v
```
