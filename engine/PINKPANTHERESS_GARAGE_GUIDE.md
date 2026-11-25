# MIDI Lab v2.2 — PinkPantheress / Garage / Eurodance Expansion

These are original-composition palettes, not recreations of melodies, drum grooves, or copyrighted samples.

## Profiles

- `pink_bedroom_2step` — intimate early garage-pop, skippy rhythmic displacement, emotionally wistful toplines, compact songs. Suggested: 125–140 BPM.
- `pink_liquid_jungle` — rolling breakbeat and melodic liquid DnB; nominal tempos 155–175 BPM, or 80–88 BPM half-time. Use a true fast rolling break, not a simple house beat with extra hats.
- `pink_y2k_eurodance` — 90s/2000s club nostalgia, glossy piano/synth stabs, bittersweet hooks, energetic bass, concise dance-pop form. Suggested: 130–150 BPM.
- `pink_fancy_club` — bright collage-like club-pop, original chopped motifs, pronounced stop/start transitions, dense and sparse contrast. Suggested: 125–145 BPM.
- `ukg_elegant_night` — late-night elegant two-step, small jazzy chords, dancing bass, few parts, big negative space. Suggested: 126–138 BPM.

## Specialized rhythm requirements for future cooks

1. UKG 2-step: asymmetric kick placements, snare/clap around beats 2 and 4, shuffled 8ths/16ths, ghost kicks and selective offbeat percussion; avoid default straight 4/4 kick patterns.
2. Liquid jungle: break-derived rhythmic cells, ghost notes, ride/shaker subdivisions, syncopated sub movement, occasional 1-bar displacement or dropped snare; avoid random velocity noise as a substitute for drum composition.
3. Eurodance: stronger club four-on-floor backbone when requested, but retain syncopated bass, little 2-step switches and emotional chord changes. Not the same rhythmic engine as 2-step.
4. Vocals: leave an intentional central-register hole for a user-recorded topline. Instrument lead works as a placeholder; a /vocal-space variant should remove that lead.
5. Originality: no copying PinkPantheress melodies, specific song samples, or signature sampled recordings. Generate original notes and program sound design in Logic.

## Engine caveat

`midilab.py` loads these five profile IDs and maps their parameters across 5 independent style roles. Its current core rhythm and voicing patterns are generic; the nuanced two-step, amen/jungle break, Eurodance four-on-floor, and vocal-space behaviors above are *creative instructions* for the composer, not fully implemented dedicated rhythm algorithms. We should build and validate these specialized drum engines in a future engine upgrade, rather than claiming these JSON profiles alone fully implement them.

## Prompt recipes

`/cook — 132 BPM, rhythm=pink_bedroom_2step, harmony=ukg_elegant_night, bass=pink_bedroom_2step, melody=pink_bedroom_2step, arrangement=pink_fancy_club, 2:30, wistful and intimate, swung two-step, four-note earworm, soft organ/piano, vocal-space=high`

`/cook — 164 BPM, rhythm=pink_liquid_jungle, bass=pink_liquid_jungle, harmony=memory_haze, melody=pink_bedroom_2step, arrangement=pink_fancy_club, 2:50, nostalgic and slightly euphoric, rolling breaks, delicate topline, tight edits`

`/cook — 142 BPM, rhythm=pink_y2k_eurodance, harmony=pink_y2k_eurodance, bass=pink_y2k_eurodance, melody=pink_bedroom_2step, arrangement=lcd_motor, 3:20, bittersweet euphoric piano stabs, garage-flavored transitions, restraint rather than stadium drop`

`/cook — 136 BPM, harmony=yl_tender_nocturne, rhythm=pink_bedroom_2step, bass=drums_solo_abysmal, melody=pink_bedroom_2step, arrangement=pink_fancy_club, 3:05, intimate melancholy guitars, skipping drums, nighttime club glow`
