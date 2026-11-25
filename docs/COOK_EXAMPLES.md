# `/cook` recipes

These are **musical design briefs**. The plugin converts supported parameters into CLI arguments; freeform descriptive phrases inform the operator's choices and sound design, but the rule-based engine does not implement every adjective as a dedicated control.

## Bittersweet minimalist motorik

```text
/cook — MIDI Lab 4.1, 116 BPM, F# minor, 6:00, style=bliss,
arc=yearning,regret,numbness,recognition,triumph,
repetition=microevolution, instrument_detail=expressive,
melodic bass, restrained plucks, same mechanical drum pattern,
production_style=midnight_motorik.
```

## Fractured synth-rock

```text
/cook — MIDI Lab 4.1, 128 BPM, F# minor, 5:00,
style=hybrid, intensity=0.85, drum_complexity=0.9, drum_mode=replace,
rigid two-bar motif, blissful harmonies, polymetric electronic percussion,
chromatic counterlines and an elegant return to minimalism,
production_style=fracture_void.
```

## Dreamy bedroom pop

```text
/cook — MIDI Lab v3, 83 BPM, A major, 3:12,
harmony=yl_kaleidoscope_pop, melody=parttime_lies_eyes_love,
a playful original repeating keyboard hook and rounded synth bass,
production_style=tape_bliss.
```

## After generating MIDI

Ask: “Analyze this MIDI and recommend a dotted-eighth delay, a tape-bliss reverb bus, and EQ per instrument.” The advisor returns settings in editable JSON and does not change the MIDI file.

## Critical constraints

- Do not request exact reproductions of existing songs. Describe instrumentation, structure, emotional progression, and effects instead.
- For `immutable` repetition, confirm the engine's loop audit before claiming the loop is bit-identical.
- The engine may not support uncommon arrangements (e.g. a 20-second ident or authentic bossa nova) without custom scripting; provide clear limitations instead of claiming the engine automatically covers them.
