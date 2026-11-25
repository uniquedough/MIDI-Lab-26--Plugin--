# MIDI LAB v2.4 — New Order taste expansion

These are **original composition behaviors**, not transcriptions. Use each as the overall `--profile` or assign different profiles to `--harmony`, `--rhythm`, `--bass`, `--melody`, `--arrangement`.

| Profile ID | Creative direction | Essential role design |
|---|---|---|
| `no_movement_cold` | 1981 post-punk sparseness and unease | stark guitars, upper melodic bass, atmospheric machine accents |
| `no_pcl_sunrise` | *Power, Corruption & Lies* 1983 optimism-with-a-bruise | bright chiming figures, melodic bass, tight hats, economical synths |
| `no_lowlife_machine_romance` | *Low-Life* 1985 human/machine fusion | low sequenced synth bass plus upper picked bass, bright synth hooks |
| `no_brotherhood_interlock` | *Brotherhood* 1986 rock-and-synth duality | ringing guitar countermelodies, bass-as-lead, live-feel drums |
| `no_technique_balearic` | *Technique* 1989 Ibiza/Balearic dance-rock | steady club motor, syncopated analog sequence, picked-bass color |
| `no_republic_afterglow` | *Republic* 1993 warm melancholic dance-pop | broad voicings, poised synths, bass replies, emotional pop motifs |
| `no_hook_bass_personality` | high-register picked melodic bass grammar | independent countermelody with articulate accents and rests |

## Core v2.4 production design

### Dual bass (New Order-specific)
Certain profiles request **separate low sequencer and high picked bass roles**. In the v2.4 generator this is implemented by a low synth bass track when `bass` is assigned `no_lowlife_machine_romance`, `no_technique_balearic`, or `no_republic_afterglow`. The existing bass track is composed in a high register with picked accents. Configure the channels with a clean picked bass and a compact mono synth/sub respectively. Neither track embeds a Program Change.

### Machine versus player
- Drum-machine kick, backbeat, sequenced low bass: very regular, small consistent velocities.
- High melodic bass: intentional picked accents and slightly variable note lengths; keep it clearly separate from sub.
- Ringing guitars: staggered chord note starts when appropriate, dynamic upper voice, short staccato counter-cells or sustained ringing notes depending on role.
- Keyboards: stable MIDI timing, harmonic voicing decisions more important than random jitter.

### Critical honesty
The MIDI generator still uses a limited authored progression family by default, and the New Order profiles act primarily through arrangement/activity parameters and additional dual-bass behavior. They do not transcribe or reproduce New Order songs, nor do they encode tone or instrument patches. MIDI performance shaping is in `performance.py`; use it with any of your previous MIDI Lab pieces.

## Prompts

`/cook — 128 BPM, harmony=no_pcl_sunrise, rhythm=no_brotherhood_interlock, bass=no_hook_bass_personality, melody=no_pcl_sunrise, arrangement=lcd_motor, 3:40, bright but lonesome, ringing guitar arpeggios, truly melodic picked bass, small synth pads, no huge choruses.`

`/cook — 123 BPM, harmony=no_republic_afterglow, rhythm=no_technique_balearic, bass=no_technique_balearic, melody=no_republic_afterglow, arrangement=no_technique_balearic, 4:05, bittersweet Balearic dance rock, syncopated synth sub bass, high picked bass counter-melody, analog chords, some guitar, late-afternoon nostalgia.`

`/cook — 119 BPM, no_lowlife_machine_romance, 3:50, trembling synth hook, motorized drums, melodic human bass, shy guitar answers, bittersweet synth-pop, final instrumental release.`

`/cook — 108 BPM, harmony=no_movement_cold, bass=no_hook_bass_personality, rhythm=no_movement_cold, melody=yl_tender_nocturne, arrangement=no_brotherhood_interlock, 4:00, bleak tender love song, lonely chiming guitars, tense picked bass, austere drum machine, intimate and unresolving.`

## Historical grounding
- Rhino: https://www.rhino.com/article/may-1983-new-order-release-power-corruption-and-lies
- DJ Mag on *Technique*: https://djmag.com/features/how-new-order-embraced-ibizas-anything-goes-energy-technique
- Song Exploder New Order transcript: https://songexploder.net/wp-content/uploads/2023/05/Song-Exploder-New-Order-Transcript.pdf
- Peter Hook on melodic high bass: https://www.guitarworld.com/artists/bassists/peter-hook-joy-division-new-order
