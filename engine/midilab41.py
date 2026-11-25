#!/usr/bin/env python3
"""MIDI Lab 4.1: removable 'fracture' textures and rhythm substitution for v4 or any Type-1 MIDI.
Original textures, no transcribed riffs. No MIDI Program Change/Bank Select.
"""
from __future__ import annotations
import argparse, json, random, math
from pathlib import Path
from mido import MidiFile, MidiTrack, Message, MetaMessage
from harmony3 import normalize_key, MODES
from analyze3 import analyze
from midilab4 import cook as cook_v4, exact_loop_test

PPQ=480
ROLES=('Fracture Drums','Bent Chord Stabs','Detuned Pluck Fragments','Industrial Percussion','Chromatic Counterline','Altered Harmony')
CHANNELS={'Fracture Drums':9,'Bent Chord Stabs':11,'Detuned Pluck Fragments':12,'Industrial Percussion':9,'Chromatic Counterline':13,'Altered Harmony':14}
EFFECTS={
 'Fracture Drums':{'suggested':'saturator > transient shaper > gated reverb (send)','notes':'Map channel 10 to a drum kit; swap sample banks, preserve MIDI groove.'},
 'Bent Chord Stabs':{'suggested':'bitcrusher > resonant bandpass > tempo delay','notes':'Pitch-bend style timbres are produced in the synth, not by changing note pitch in MIDI.'},
 'Detuned Pluck Fragments':{'suggested':'ring mod > chorus > ping-pong delay','notes':'Assign to a percussive FM synth with short envelope.'},
 'Industrial Percussion':{'suggested':'noise synth > distortion > short metallic reverb','notes':'Map GM percussion note numbers or customize sampler mapping.'},
 'Altered Harmony':{'suggested':'detuned poly synth > phaser > long reverb send','notes':'Extended chords and chromatic mediants; automate wetness independently.'},
 'Chromatic Counterline':{'suggested':'mono synth > mild overdrive > flanger','notes':'Keep below lead in mix; the counterline is optional.'}
}

def ticks(bar,beat=0):return int(round((bar*4+beat)*PPQ))

def note(events,name,start,beats,pitch,velocity):
    start=max(0,int(start));end=start+max(1,round(beats*PPQ))
    if not (0<=pitch<=127):return
    ch=CHANNELS[name]
    events[name].append((start,True,pitch,int(max(1,min(127,velocity))),ch))
    events[name].append((end,False,pitch,0,ch))

def add_track(mid,name,events):
    tr=MidiTrack();tr.append(MetaMessage('track_name',name=name,time=0));last=0
    # note-offs before note-ons at coincident position, avoiding same-pitch overlap
    for abs_t,is_on,pitch,vel,ch in sorted(events,key=lambda e:(e[0],e[1],e[2])):
        tr.append(Message('note_on' if is_on else 'note_off',note=pitch,velocity=vel,channel=ch,time=abs_t-last))
        last=abs_t
    mid.tracks.append(tr)

def get_track_name(track):return next((m.name for m in track if m.is_meta and m.type=='track_name'),'')

def get_length(mid):
    return max((sum(msg.time for msg in tr) for tr in mid.tracks),default=0)

def pitch_class(key):
    # parse_key may return tuple or pc; use v3 composer convention
    x=normalize_key(key)
    return x[0] if isinstance(x,tuple) else x

def build_layers(total_bars,key,mode,style,intensity,drum_complexity,seed,drum_mode):
    if style not in ('minimal','bliss','fracture','hybrid'):raise ValueError('bad style')
    rng=random.Random(seed);events={k:[] for k in ROLES}
    tonic=pitch_class(key)
    scale=MODES[mode]
    def scale_pitch(degree,octave=4):return 12*(octave+1)+tonic+scale[degree%7]+12*(degree//7)
    # Density envelope: hybrid evolves through calm > bliss > fracture > integration > calm.
    def activity(bar):
        section=min(4, int(5*bar/max(1,total_bars)))
        multipliers={'minimal':[.06,.09,.04,.09,.04], 'bliss':[.1,.15,.1,.16,.08],
                     'fracture':[.75,.86,.95,.91,.82], 'hybrid':[.04,.2,.85,.53,.07]}
        return multipliers[style][section]*intensity, section
    # Rhythm shapes deliberately recur in 7/8 and 5/8 against a 4/4 foundation; no tempo/time-signature mutation.
    # These are note-grid overlays (7/8=3.5 quarter beats; 5/8=2.5 quarter beats).
    phrase_library=[(0,.75,1.25,2.75),(0,.5,1.75,2.5,3.25),(0,1.5,2.25,3.5)]
    chord_sets=[(-1,2,4),(0,2,5),(0,3,6),(-1,1,4)]
    for bar in range(total_bars):
        a,section=activity(bar)
        a=min(1,a)
        if a<=0:continue
        # Constant motifs are intentionally separate from drum and bass anchors.
        if style!='minimal' and rng.random()<min(.96,a*1.8):
            pattern=phrase_library[(bar//4)%len(phrase_library)]
            tones=chord_sets[(bar//8)%len(chord_sets)]
            for i,d in enumerate(tones):
                if rng.random()<(.58+a*.35):
                    # alternate diatonic / upper-neighbor tensions
                    p=scale_pitch(d%7,4 if i<2 else 5)+(1 if (section==2 and i==1) else 0)
                    note(events,'Bent Chord Stabs',ticks(bar,pattern[i%len(pattern)]),.15+rng.choice([0,.10,.22]),p,44+int(38*a)+i*3)
        if rng.random()<min(.90,a*1.5):
            # Repeating off-grid phrase: intentionally limited pitch set and a semitone rub on the tension phase.
            for beat,degree in ((.75,4),(2.25,3),(3.25,2)):
                if rng.random()<(0.4+a*.55):
                    p=scale_pitch(degree,5)+(1 if section==2 and degree==3 else 0)
                    note(events,'Detuned Pluck Fragments',ticks(bar,beat),.12 if section==2 else .28,p,37+int(35*a))
        if style in ('fracture','hybrid') and drum_mode!='off':
            # Industrial percussion is a removable supplemental layer, always on drum channel.
            if rng.random()<a*drum_complexity*1.3:
                for b in rng.sample([0,.25,.75,1.25,1.75,2.5,3.25,3.75],k=3):
                    if rng.random()<drum_complexity:
                        note(events,'Industrial Percussion',ticks(bar,b),.09,rng.choice([37,39,56,75]),36+int(45*a))
        # Altered chord color: chord *families*, not arbitrary stacked notes. 8-bar changes.
        # Intervals below are relative to tonic pitch class; they include b9, #11,
        # minor-major-7 and chromatic-mediant voicings. Voice space is intentional.
        if style in ('fracture','hybrid') and a>.35 and bar%8==0:
            voicings=((0,3,7,11,14),  # minor-major9
                      (3,7,11,14,18), # chromatic mediant minor9(#11)
                      (8,11,15,18,22),# bright alien major7(#11) color
                      (1,5,8,11,15)) # displaced altered dominant/suspension
            chord=voicings[(bar//8)%len(voicings)]
            for i,interval in enumerate(chord):
                # One stable chord per eight-bar span. Expansive notes are distributed
                # over the first two beats, and sustained to convey broad harmony.
                note(events,'Altered Harmony',ticks(bar,0 if i<3 else .5),
                     5.75 if i<3 else 5.25,48+tonic+interval,
                     31+int(31*a)-i*2)
        if style in ('fracture','hybrid') and a>.3 and bar%4==0 and rng.random()<a:
            # Chromatic neighbor clusters resolve to scale tones, not random chromatic soup.
            target=scale_pitch(4,4);pitches=[target+1,target,target-2,target]
            for i,p in enumerate(pitches):
                note(events,'Chromatic Counterline',ticks(bar, .25+i*.75),.27,p,47+int(a*26))
    if drum_mode=='replace':
        # Anchored, but intricate: 7/8 hats against 4/4 snare/kick, plus 5/8 percussion.
        # velocity fixed within repeating 28-beat supercycle (LCM of 4 and 3.5), no random fills.
        end=total_bars*4
        for b in range(end):
            note(events,'Fracture Drums',round(b*PPQ),.10,36,90 if b%4==0 else 71)
            if b%4 in (1,3):note(events,'Fracture Drums',round(b*PPQ),.10,38,78)
        for i in range(int(end/3.5)+1):
            start=i*3.5
            for offset,pitch,v in ((0,42,55),(.5,42,36),(1.25,46,63),(2.0,42,44),(2.75,42,50),(3.25,42,30)):
                if start+offset<end:note(events,'Fracture Drums',round((start+offset)*PPQ),.07,pitch,v)
        if drum_complexity>=.45:
            for i in range(int(end/2.5)+1):
                t=i*2.5+1.75
                if t<end:note(events,'Fracture Drums',round(t*PPQ),.07,39,43)
    # Avoid tails beyond arrangement grid and same-pitch collision due to offsets at repeats.
    limit=ticks(total_bars)
    for k,ev in events.items():
        starts={};clean=[]
        for t,on,p,v,ch in sorted(ev,key=lambda e:(e[0],e[1],e[2])):
            if on:
                if t>=limit:continue
                token=(ch,p)
                # For identical notes in same role, close current before retrigger if necessary.
                if token in starts:
                    clean.append((t,False,p,0,ch));starts.pop(token)
                starts[token]=t;clean.append((t,True,p,v,ch))
            else:
                if (ch,p) in starts:
                    clean.append((min(t,limit),False,p,0,ch));starts.pop((ch,p))
        for (ch,p) in starts:clean.append((limit,False,p,0,ch))
        events[k]=clean
    return events

def patch(source,output,style='hybrid',intensity=.75,drum_complexity=.8,drum_mode='keep',seed=41,key='F#',mode='minor'):
    source=Path(source);output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    mid=MidiFile(source)
    if mid.type!=1 or mid.ticks_per_beat!=PPQ:raise ValueError('Input must be MIDI Type 1, 480 PPQ')
    if not 0<=intensity<=1 or not 0<=drum_complexity<=1:raise ValueError('intensity and drum-complexity must be 0..1')
    if drum_mode not in ('keep','replace','off'):raise ValueError('drum_mode must be keep, replace, or off')
    if mode not in MODES:raise ValueError('Unsupported mode')
    original_tracks={get_track_name(t):[m.copy(time=m.time) for m in t] for t in mid.tracks}
    source_track_names=[get_track_name(t) for t in mid.tracks]
    # Ensure repeat patching is idempotent: strip only our own overlay tracks.
    mid.tracks=[tr for tr in mid.tracks if get_track_name(tr) not in ROLES]
    if drum_mode=='replace':
        mid.tracks=[tr for tr in mid.tracks if get_track_name(tr) not in ('Loop Drums','Drum Engine')]
    end=get_length(mid)
    # MIDI may end with held notes slightly later than grid; infer rounded 4/4 bar count.
    total_bars=max(1,round(end/(4*PPQ)))
    layers=build_layers(total_bars,key,mode,style,intensity,drum_complexity,seed,drum_mode)
    for name,events in layers.items():
        if events:add_track(mid,name,events)
    mid.save(output)
    report=analyze(output)
    if not report['technical_pass']:raise RuntimeError('MIDI audit failed: '+str(report['validation']))
    # Compare original anchor note-on/off stream to patched anchor; any removal is an error.
    locks={}
    for name in ('Immutable Pulse',):
        if name in source_track_names:
            orig=next(t for t in MidiFile(source).tracks if get_track_name(t)==name)
            after=next(t for t in mid.tracks if get_track_name(t)==name)
            locks[name]=[m.dict() for m in orig]==[m.dict() for m in after]
            if not locks[name]:raise RuntimeError('Locked anchor modified')
    if drum_mode=='keep' and 'Loop Drums' in source_track_names:
        orig=next(t for t in MidiFile(source).tracks if get_track_name(t)=='Loop Drums')
        after=next(t for t in mid.tracks if get_track_name(t)=='Loop Drums')
        locks['Loop Drums']=[m.dict() for m in orig]==[m.dict() for m in after]
        if not locks['Loop Drums']:raise RuntimeError('Locked drums modified')
    report_path=output.with_suffix('.audit.json');report_path.write_text(json.dumps(report,indent=2))
    recipe=output.with_suffix('.texture_recipe.json')
    recipe.write_text(json.dumps({'schema':'MIDI_LAB_4.1','input':source.name,'style':style,'intensity':intensity,
                'drum_complexity':drum_complexity,'drum_mode':drum_mode,'seed':seed,'key':key,'mode':mode,
                'source_anchor_locks':locks,'added_roles':{k:len(v)//2 for k,v in layers.items() if v},
                'effects_are_recommendations_not_embedded_audio':True,'effects':EFFECTS},indent=2))
    return {'midi':str(output),'audit':str(report_path),'texture_recipe':str(recipe),
            'notes':report['note_count'],'new_tracks':[k for k,v in layers.items() if v],
            'anchors_preserved':locks,'technical_pass':True}

def main():
    p=argparse.ArgumentParser(description='MIDI Lab 4.1 removable fractured rhythms, bent harmony and sparse-to-complex textures')
    sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('patch',help='Augment any existing v3/v4 Type-1 480PPQ MIDI')
    a.add_argument('--input',required=True,type=Path);a.add_argument('--output',required=True,type=Path)
    a.add_argument('--key',default='F#');a.add_argument('--mode',default='minor')
    c=sub.add_parser('cook',help='Generate a fresh v4 composition then apply 4.1 overlays')
    c.add_argument('--output',required=True,type=Path)
    c.add_argument('--bpm',type=int,default=116);c.add_argument('--minutes',type=float,default=4)
    c.add_argument('--key',default='F#');c.add_argument('--mode',default='minor')
    c.add_argument('--arc',default='yearning,regret,numbness,recognition,triumph')
    c.add_argument('--repetition',choices=['immutable','microevolution','phase'],default='microevolution')
    c.add_argument('--instrument-detail',choices=['machine','natural','expressive'],default='expressive')
    c.add_argument('--profile',default='yl_tender_nocturne')
    c.add_argument('--harmony',default='yl_tender_nocturne');c.add_argument('--rhythm',default='lcd_motor')
    c.add_argument('--bass',default='no_hook_bass_personality');c.add_argument('--melody',default='drums_solo_jonny')
    c.add_argument('--arrangement',default='lcd_motor')
    for parser in (a,c):
        parser.add_argument('--style',choices=['minimal','bliss','fracture','hybrid'],default='hybrid')
        parser.add_argument('--intensity',type=float,default=.8)
        parser.add_argument('--drum-complexity',type=float,default=.85)
        parser.add_argument('--drum-mode',choices=['keep','replace','off'],default='keep')
        parser.add_argument('--seed',type=int,default=41)
    args=p.parse_args()
    if args.command=='cook':
        from types import SimpleNamespace
        base=args.output.with_name(args.output.stem+'_base_v4.mid')
        req=SimpleNamespace(bpm=args.bpm,minutes=args.minutes,key=args.key,mode=args.mode,
            arc=args.arc,repetition=args.repetition,instrument_detail=args.instrument_detail,
            profile=args.profile,harmony=args.harmony,rhythm=args.rhythm,bass=args.bass,melody=args.melody,
            arrangement=args.arrangement,drums='minimal',mood='tender',seed=args.seed,
            variant='restrained',weirdness='3,4,2,2,4',anchor='synth',output=base)
        cook_v4(req)
        source=base
    else:source=args.input
    print(json.dumps(patch(source,args.output,args.style,args.intensity,args.drum_complexity,
                           args.drum_mode,args.seed,args.key,args.mode),indent=2))
if __name__=='__main__':main()
