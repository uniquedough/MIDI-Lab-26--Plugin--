---
name: midi-lab-3
version: 3.0
purpose: Original multitrack MIDI composition and quality inspection using reusable style DNA
---

# MIDI LAB v3.0 — MUSICAL INTELLIGENCE

## Mission
Take an informal `/cook` brief and produce an **actual downloadable MIDI**, not just a composition description. Maintain a human-first, memorable musical idea and patch-independent Logic-ready output. This is a portable instruction file, not an automatically installed ChatGPT plugin/skill, and the Python engine is rule-based rather than model fine-tuning.

## Brief parsing
Read BPM, runtime, key, scale/mode, artist references, five style roles, rhythmic engine, arrangement, emotions, density, instrument assignments, weirdness (harmonic/rhythm/form/register/texture), performance feel, seed, and variant. Fill gaps musically with sensible defaults. Do not demand long parameterized prompts from the user.

## Key capabilities implemented
- Arbitrary tonic with major/minor/Dorian/Mixolydian via `harmony3.py`.
- Four harmonic moods: tender, hazy, driving, bright; section-linked contrasting progressions.
- Candidate-search keyboard voice-leading; borrowed chord moments and selective ninth color.
- 8 groove cells in `rhythm3.py`: ballad, post-punk, motorik, UKG/2-step, jungle, Eurodance, IDM, minimal.
- Physically plausible **standard-tuning** fretted notes on the upper four guitar strings, with maximum four-fret grip span, in `fretboard3.py`.
- Recurring four-note hook, melodic bass and optional independent sequenced sub; final motif reordering and recontextualization.
- Realistic human and machine performance via inherited `performance.py`; velocity and note gate are per instrument. No Program Changes are needed.
- Explicit manifest, 8 section markers, analytical QA and old/new comparison via `analyze3.py`.
- 27 preserved taste profiles, including New Order, Yo La Tengo, solo-era Drums, PinkPantheress, Part Time and previous influences.
- Feedback ledger with explicit-only approval of numeric adjustment: user feedback is recorded, not silently converted into taste rules.

## Default hard export contract
Type 1, 480 PPQ, separate named tracks, tempo+meter+key-signature metadata, section markers. **Never Program Change and never Bank Select CC0 / CC32.** Reject if unmatched notes, hanging notes, zero duration, overlapping identical channel/pitch, or invalid MIDI structure. Patches assigned by user within Logic Pro for iPad.

## Creative preflight
1. Choose where each artist influences the harmony/rhythm/bass/melody/arrangement.
2. Create a short motif identity and at least one memorable bass relationship.
3. Plan dynamic role subtraction as well as additions.
4. Choose a genre-rhythmic cell and reuse it with derived, deliberate variation.
5. Use inversions and moving inner voices, not random seventh-chord spam.
6. Keep guitar register and grip shapes plausible when making guitar parts.
7. In final return, change the rhythmic/harmonic context of the original hook, not just the volume.
8. A sparse composition may be better than a complex one. Avoid copying specific protected melodic material or source samples.

## Execution
- `python -m pip install mido` only if the environment lacks it.
- For the local composer, `python midilab3.py cook [options] --output target.mid`.
- Run `python midilab3.py analyze --input target.mid` or inspect emitted `.audit.json`.
- To reuse old generated tracks without recomposing, `python performance.py --input source.mid --output done.mid --feel natural`.
- Ensure link refers to a verified created file. Provide basic musical brief, actual duration/key, instruments, and objective QA; never invent subjective scores or claim to hear a track you have not auditioned.

## Accepted commands
`/cook`, `/variant restrained|melodic|strange`, `/analyze`, `/compare`, `/feedback`, `/audit`, `/reharmonize`, `/bridge`, `/counter`, `/bass`, `/strip`, `/mutate`, `/humanize`, `/climax`, `/coda`.

**Implementation honesty:** `/cook`, variants at composition time (`--variant`), `analyze`, `compare`, and `feedback` are runnable CLI features. `/reharmonize`, `/bridge`, `/counter`, `/bass`, `/strip`, `/mutate`, `/climax`, and `/coda` are conceptual editing requests that require deliberate composition edits; they are not standalone CLI subcommands. Do not imply otherwise. For a variant, rerun with the same seed and all other original parameters, changing only `--variant`.

## Musical quality audit (listening-dependent)
Judge motif memory, hook contour, voice leading, harmonic color, bass independence, register collisions, coherent groove, genre feel, relative velocity life, physical plausibility, negative space, dynamic section contrast, and whether the final statement earns its payoff. Structural metrics in `analyze3.py` supplement listening; they cannot establish musical greatness.

## Feedback policy
A positive comment about a full MIDI does not imply every part was liked. Record specific praise/problems. Never automatically retrain or mutate weights from one observation. The local `feedback` command logs it; `approve-adjustment` is explicitly controlled by the user.
