# Composer API and CLI

## MCP tools

`cook_midi`: `title`, `bpm`, `minutes`, `key` required. Optional `engine` = `v3`, `v4`, `v4.1` (default); `mode` = `major`, `minor`, `dorian`, `mixolydian`; individual `profile`, `harmony`, `rhythm`, `bass`, `melody`, `arrangement`; `arc` (comma-separated emotional stages); `repetition` = `immutable`, `microevolution`, `phase`; `instrument_detail` = `machine`, `natural`, `expressive`; `style` = `minimal`, `bliss`, `fracture`, `hybrid`; `drum_mode` = `keep`, `replace`, `off`; `intensity`, `drum_complexity` = 0 to 1; `seed`; and `production_style` = one of the effects presets.

Only v3 supports `drums` and `performance` through `cook_midi`; v4 and v4.1 use their own corresponding fields. v4.1's `replace` option generates polymetric overlays against a **4/4** underlying song grid; it does not change global meter.

`list_profiles`: lists supported taste profile identifiers and effects presets.

`analyze_midi`: `{ "path": "/full/path/song.mid" }`.

`advise_effects`: `{ "path": "/full/path/song.mid", "preset": "tape_bliss" }`.

`patch_textures`: `{ "path": "/full/path/song.mid", "title": "My Fracture Mix", "style": "hybrid", "drum_mode": "keep" }`.

## Direct CLI

```bash
# v3 conventional songwriter
python engine/midilab3.py cook --bpm 127 --minutes 4 --key E --mode minor \
  --harmony yl_tender_nocturne --bass no_hook_bass_personality \
  --drums motorik --performance neworder --output v3_song.mid

# v4 emotional loop
python engine/midilab4.py cook --bpm 94 --minutes 8 --key B --mode minor \
  --arc regret,numbness,recognition,acceptance,triumph \
  --repetition immutable --instrument-detail natural --output v4_loop.mid

# v4.1 hybrid
python engine/midilab41.py cook --bpm 128 --minutes 5 --key 'F#' --mode minor \
  --style hybrid --drum-mode replace --intensity 0.85 \
  --drum-complexity 0.9 --output hybrid.mid

# v4.1 non-destructive layer patching
python engine/midilab41.py patch --input v3_song.mid --output v3_song_fractured.mid \
  --style fracture --drum-mode keep

# v4.2 effects recommendation (non-destructive)
python engine/effects42.py v3_song.mid --preset tape_bliss

# MIDI analysis
python engine/midilab3.py analyze --input v3_song.mid --output analysis.json
```

## Effects presets

`bossa_afterglow`, `tape_bliss`, `rigid_machine`, `fracture_void`, `broadcast_ident`, `midnight_motorik`.

At BPM = `b`, a dotted-eighth delay is `45000/b` ms. Set delay sync to 3/16 or enter the calculated time manually.

## Integrity

The MCP server performs a forbidden-event scan on output MIDI. The original engine generates sidecar audit reports with additional checks. MIDI effects are never baked into notes or rendered automatically.
