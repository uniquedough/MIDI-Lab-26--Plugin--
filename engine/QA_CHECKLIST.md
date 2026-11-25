# MIDI Lab 3.0 QA

## Mandatory technical
- Type 1 and 480 PPQ.
- BPM, meter, section markers, track naming and no negative delta times.
- No Program Change; no Bank Select CC0/32.
- No unmatched note-off, hanging notes, zero-length notes or same-channel same-note overlaps.
- If `--performance` was applied, compare processed velocities with intended instrument roles.

## Objective structural / conceptual checks
- Manifest contains declared key, mode, separate role assignments, chosen drum engine and harmonic sequence.
- Chord voicings have bounded leaps/compact register; no unintentional chord collisions.
- Guitar positions record standard EADGBE tuning and feasible four-fret grips on upper strings.
- Groove pattern fits the genre; UKG includes shifted offbeats, jungle includes subdivided break, motorik stays anchored.
- Bass has rhythmic and melodic identity; synth bass is separate where intended.
- Four-note motif returns, mutates, and changes context in final section.
- Sparse sections genuinely subtract parts.
- Different variants retain the harmonic and melodic seed.

## Human listening review — not automatically provable
- Does melody survive if played alone?
- Are chords moving emotionally, or merely accumulating extensions?
- Is bass musical even without drums?
- Is rhythm stylistically credible, and are repeats hypnotic rather than monotonous?
- Would fewer layers make the song stronger?
- Is guitar articulation actually convincing in the selected Logic sound?
- Did the climax earn its arrival through form, not velocity?
- Do the actual velocity layers and effects in Logic make the performance believable?
