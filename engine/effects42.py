#!/usr/bin/env python3
"""MIDI Lab 4.2: MIDI-aware, DAW-agnostic sound-design advice for Logic.
Never edits MIDI. Effects cannot be embedded as audio in a MIDI file.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from mido import MidiFile

PRESETS={
 'bossa_afterglow': {'mood':'warm bittersweet dance / gentle bossa','space':'small, warm room with haze on melodic ornaments','accent':'dotted-eighth guitar echoes become the rhythmic ornament'},
 'tape_bliss': {'mood':'detuned nostalgic warmth','space':'washed reverb and slow stereo movement','accent':'soft chorus and restrained tape-style modulation'},
 'rigid_machine': {'mood':'dry mechanical dance-rock','space':'tight front-of-mix focus','accent':'short envelopes and gated accents, little reverb'},
 'fracture_void': {'mood':'angular, distorted electronic experimentalism','space':'contrasting bone-dry hits and isolated long tails','accent':'bitcrushing, resonant filtering, rhythmic echo'},
 'broadcast_ident': {'mood':'glossy late-1980s television ident','space':'bright digital room and gated accents','accent':'shimmering bell trails and final sustained stereo pad'},
 'midnight_motorik': {'mood':'hypnotic melancholic electronic indie','space':'large atmosphere around a small, precise pulse','accent':'layering and automation instead of drum fills'},
}

def delay_ms(bpm):
    beat=60000.0/bpm
    return {'quarter':round(beat,2),'eighth':round(beat/2,2),'dotted_eighth':round(beat*.75,2),'sixteenth':round(beat/4,2),'dotted_quarter':round(beat*1.5,2),'triplet_eighth':round(beat/3,2)}

def analyze_midi(path):
    mid=MidiFile(str(path))
    ppq=mid.ticks_per_beat
    tempo=500000
    candidates=[]
    for tr in mid.tracks:
        t=0
        for msg in tr:
            t+=msg.time
            if msg.type=='set_tempo':candidates.append((t,msg.tempo))
    if candidates:
        tempo=sorted(candidates)[0][1]
    bpm=60000000/tempo
    tracks=[]
    for i,tr in enumerate(mid.tracks):
        name=next((x.name for x in tr if x.type=='track_name'),f'Track {i+1}')
        notes=[x for x in tr if x.type=='note_on' and x.velocity>0]
        if notes:
            drum=any(x.channel==9 for x in notes) or bool(re.search(r'drum|shaker|ride|brush|percussion|stick|kick|snare|hat',name,re.I))
            tracks.append({'name':name,'notes':len(notes),'drum':drum,'channels':sorted(set(x.channel+1 for x in notes))})
    return {'filename':Path(path).name,'bpm':round(bpm,4),'ppq':ppq,'midi_type':mid.type,'tracks':tracks}

def classify(name,drum):
    n=name.lower()
    if drum:
        return 'light_percussion' if any(x in n for x in ('shaker','ride','brush','stick')) else 'drums'
    for words,role in [(('nylon','guitar','strum'),'guitar'),(('rhodes','piano','key','organ'),'keys'),(('vibra','bell','mallet'),'bells'),(('bass','thumb'),'bass'),(('choir','pad','upper','harmon'),'pad'),(('pluck','motif','lead','synth'),'lead')]:
        if any(w in n for w in words):return role
    return 'lead'

BASE={
 'guitar':[{'effect':'Channel EQ','settings':'HPF 80–110 Hz; gentle dip at 250–350 Hz if boxy'},{'effect':'Compressor','settings':'2:1; 2–3 dB gain reduction on peaks'}],
 'bass':[{'effect':'Channel EQ','settings':'HPF 30–40 Hz; narrow cut around 200–300 Hz if muddy'},{'effect':'Compressor','settings':'2.5:1; 3–5 dB gain reduction; preserve initial attack'}],
 'keys':[{'effect':'Channel EQ','settings':'HPF 90–130 Hz; keep warm mids'},{'effect':'Chorus / Ensemble','settings':'Slow rate 0.2–0.5 Hz, subtle wetness'}],
 'bells':[{'effect':'Channel EQ','settings':'HPF 180–240 Hz; soften harsh 3–6 kHz only if necessary'}],
 'pad':[{'effect':'Channel EQ','settings':'HPF 150–220 Hz; leave space for bass and lead'}],
 'lead':[{'effect':'Channel EQ','settings':'HPF 100–180 Hz; tame sharp resonances if needed'}],
 'drums':[{'effect':'Channel EQ','settings':'Clean unwanted low rumble; do not thin the kick'}],
 'light_percussion':[{'effect':'Channel EQ','settings':'HPF 180–300 Hz; tame sharp highs if needed'}],
}

def build_chain(role,preset,bpm):
    chain=[dict(x) for x in BASE[role]]
    delay={'effect':'Stereo Delay','settings':f'Dotted eighth (3/16), {delay_ms(bpm)["dotted_eighth"]:.2f} ms at {bpm:.2f} BPM; feedback 15–24%; wet 13–23%; low-cut 280 Hz, high-cut 4.5 kHz; tempo sync ON'}
    if preset=='bossa_afterglow':
        if role=='guitar':chain += [delay,{'effect':'ChromaVerb (aux send)','settings':'Warm room/plate, 1.2–1.7 s; pre-delay 15–25 ms; send modestly'}]
        elif role=='bells':chain += [{'effect':'Stereo Delay','settings':'1/8 or dotted 1/8; feedback 10–18%; wet 9–16%; high-cut 5 kHz'},{'effect':'ChromaVerb (aux send)','settings':'Soft plate 1.7–2.3 s; 20–30 ms pre-delay'}]
        elif role=='keys':chain += [{'effect':'Tape Delay','settings':f'1/8 ({delay_ms(bpm)["eighth"]} ms); feedback 8–15%; wet 8–12%; soften top end'},{'effect':'ChromaVerb (aux send)','settings':'Small warm plate, 1.3–1.8 s'}]
        elif role in ('drums','light_percussion'):chain += [{'effect':'ChromaVerb (aux send)','settings':'Short room 0.5–0.9 s; very low send; keep groove intimate'}]
        elif role=='bass':chain += [{'effect':'Saturation / soft drive','settings':'Subtle harmonics, level-match bypass; retain rounded fundamental'}]
        else:chain.append({'effect':'ChromaVerb (aux send)','settings':'Warm plate 1.2–1.8 s, conservative send'})
    elif preset=='rigid_machine':
        chain.append({'effect':'Overdrive or saturation','settings':'Low drive, level matched; emphasize attack, keep mostly dry'} )
        if role not in ('bass','drums'):chain.append({'effect':'Noise Gate','settings':'Short release; tune threshold so notes still sound natural'})
    elif preset=='fracture_void':
        if role not in ('bass','drums'):chain += [{'effect':'Bitcrusher','settings':'10–12 bit; downsampling 1–3x; blend or automate in phrases'},delay,{'effect':'AutoFilter / filter automation','settings':'Resonant bandpass sweep; control intensity section-by-section'}]
        else:chain.append({'effect':'Distortion / parallel bus','settings':'Parallel blend 10–25%; do not destroy transient clarity'})
    elif preset=='broadcast_ident':
        chain += [{'effect':'ChromaVerb','settings':'Digital plate or bright chamber 1.4–2.5 s; on final chord consider longer tail'}]
        if role in ('bells','lead'):chain.append({'effect':'Stereo Delay','settings':'1/8; feedback 12%; wet 12%; end logo shimmer'})
    elif preset=='midnight_motorik':
        if role in ('lead','pad','keys','bells'):chain += [{'effect':'Chorus / ensemble','settings':'Low rate 0.2–0.4 Hz; modest depth'},{'effect':'ChromaVerb (aux send)','settings':'2.4–3.6 s; high-pass reverb at 300 Hz'}]
    else:
        if role in ('lead','pad','keys','bells','guitar'):chain += [{'effect':'Chorus','settings':'Very subtle movement'},{'effect':'ChromaVerb (aux send)','settings':'Warm plate 1.7–2.6 s; cut lows from return'}]
    return chain

def make_recipe(path,preset='bossa_afterglow'):
    if preset not in PRESETS:raise ValueError(f'Unknown preset {preset}')
    x=analyze_midi(path)
    entries=[]
    for tr in x['tracks']:
        role=classify(tr['name'],tr['drum'])
        entries.append({**tr,'role':role,'insert_and_send_chain':build_chain(role,preset,x['bpm']),
                        'advice':'Try delay on a duplicated guitar/pluck track at low wetness, not on every instrument.' if preset=='bossa_afterglow' and role=='guitar' else 'Set instrument patch manually in Logic; recipe is guidance, not an embedded FX preset.'})
    return {'schema':'midi-lab-effects-4.2','source':x['filename'],'tempo_bpm':x['bpm'],'preset':preset,
            'character':PRESETS[preset], 'sync_delays_ms':delay_ms(x['bpm']),
            'tracks':entries,
            'mix_guidance':['Use send reverb to create shared space; keep the kick and bass comparatively dry.',
                            'Start with wet effects off, then raise until just audible; level-match when comparing.',
                            'Automate filter cutoff, send level, or delay feedback at emotional transition points.',
                            'Delay repeats are audio, NOT additional MIDI notes; check that repeats do not clutter the groove.',
                            'MIDI Lab does not install plug-ins or apply effects automatically.'],
            'logic_notes':'All recommendations can be approximated with stock Logic Pro effects. Exact plug-in names and options may differ on Logic for iPad versus Mac.',
            'midi_modified':False}

def main():
    p=argparse.ArgumentParser(description='MIDI Lab 4.2 sound design advisor (read-only for MIDI)')
    p.add_argument('midi',type=Path)
    p.add_argument('--preset',choices=sorted(PRESETS),default='bossa_afterglow')
    p.add_argument('--output',type=Path)
    p.add_argument('--all-presets',action='store_true')
    args=p.parse_args()
    if args.all_presets:
        data={'source':args.midi.name,'presets':{k:make_recipe(args.midi,k) for k in PRESETS}}
    else:data=make_recipe(args.midi,args.preset)
    dest=args.output or args.midi.with_suffix('.effects42.json')
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'Wrote {dest}; tempo {analyze_midi(args.midi)["bpm"]:.2f} BPM; MIDI unchanged')

if __name__=='__main__':main()
