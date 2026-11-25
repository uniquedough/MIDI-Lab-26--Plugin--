# MIDI Lab v3.0 — Technical release notes

2026-10-14 — First complete v3 Musical Intelligence build.

- Preserved all **27** style profiles from v2.4 and explicit taste ledger; no silent retraining.
- Added all-tonic four-mode harmony generation (major, natural minor, Dorian, Mixolydian).
- Added keyboard voice-leading with search across candidate four-note voicings.
- Added purposeful modal borrowing in middle and final sections and occasional replace-fifth-with-ninth harmony color.
- Added genuinely distinct genre drum engines: ballad, postpunk, motorik, UKG/2step, jungle, Eurodance, IDM, minimalist.
- Added physically plausible standard-tuning picked guitar shapes and declared frets in manifest.
- Added motif-recall and final reinterpretation, explicit density contrast and negative-space bridge.
- Preserved v2.4 per-instrument velocity, timing and gate-shaping; postprocessing can be applied to old MIDI.
- Added harmonic/meter/track/arrangement manifests and v3 analyzer with groove/velocity/interval features.
- Added compare function and local feedback capture + explicit approval of tasteful weight changes.
- Tested deterministic variants and three original demos against technical MIDI audits.
- All 8 unit tests pass, including 12 tonal centers x 4 modes.

## Known boundaries

1. Supports 4/4 compositions by default, not arbitrary meter generation.
2. Not a trained model or a sample-instrument renderer. Source prompts choose symbolic traits; a Logic instrument performs them.
3. Guitar shape selection is limited to the top four standard-tuned strings and is a reachability heuristic, not a biomechanical simulation.
4. V3 has a vocabulary of authored harmonic families and rhythmic cells; producing completely novel structural forms still requires human/AI composition decisions.
5. Comparisons report measurable MIDI changes; they do not objectively grade taste or emotional quality.
