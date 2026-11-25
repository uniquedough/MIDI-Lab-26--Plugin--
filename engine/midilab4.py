#!/usr/bin/env python3
"""MIDI Lab 4.0 - expression, emotional arcs and verifiable loop invariants.
Backward-compatible extension: use midilab3.py for every v3 command.
"""
from __future__ import annotations
import argparse, json, math, random, collections
from pathlib import Path
from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo
from midilab3 import ComposerV3, PPQ, ROLE_CHANNEL
from harmony3 import MODES, degree_chord, voice_lead, bass_root
from analyze3 import analyze

EMOTIONS={
 'regret':{'register':-5,'density':.45,'color':'minor9','velocity':-6},
 'numbness':{'register':-12,'density':.24,'color':'sus','velocity':-13},
 'recognition':{'register':0,'density':.57,'color':'add9','velocity':0},
 'acceptance':{'register':2,'density':.58,'color':'major6','velocity':-2},
 'triumph':{'register':7,'density':.74,'color':'sixth','velocity':4},
 'yearning':{'register':4,'density':.59,'color':'sus','velocity':-1},
 'unease':{'register':-2,'density':.48,'color':'b2','velocity':-5},
 'tenderness':{'register':0,'density':.43,'color':'add9','velocity':-7},
}

class ComposerV4(ComposerV3):
    def __init__(self,*args,emotional_arc='regret,numbness,recognition,acceptance,triumph',
                 repetition='microevolution',anchor='synth',drum_lock=False,
                 instrument_detail='expressive',**kwargs):
        super().__init__(*args,**kwargs)
        if self.total_bars % 2:
            self.total_bars += 1
            self.sections = self._sections()
        self.arc=[x.strip().lower() for x in emotional_arc.split(',')]
        if not self.arc or any(x not in EMOTIONS for x in self.arc):raise ValueError('Unknown emotion')
        if repetition not in ('immutable','microevolution','phase'):raise ValueError('Unknown repetition mode')
        if anchor not in ('synth','bass','none'):raise ValueError('Unknown anchor')
        if instrument_detail not in ('machine','natural','expressive'):raise ValueError('Unknown performance detail')
        self.repetition=repetition;self.anchor=anchor;self.drum_lock=drum_lock
        self.instrument_detail=instrument_detail
        self.emotional_log=[];self.phase_cycles=(3,4,5)
        self.loop_bars=2
        self.anchor_pattern=[(0,0,.50,76),(1.5,0,.28,67),(2.0,0,.46,74),(3.5,0,.25,66)]
        self.drum_pattern=[(0,36,87,.09),(.5,42,45,.07),(1,38,74,.08),(1.5,42,39,.07),(2,36,81,.09),(2.5,42,43,.07),(3,38,74,.08),(3.5,42,39,.07)]
        self.low_note=35 # B1 for B minor, computed below
        self.low_note=35+self.key_pc-11
        while self.low_note<31:self.low_note+=12
        while self.low_note>47:self.low_note-=12
        self.events['Immutable Pulse']=[]
        self.events['Loop Drums']=[]
        self.events['Memory Plucks']=[]
        self.events['Slow Upper Voices']=[]
        self.events['Expressive Bass']=[]
        self.events['Companion Guitar']=[]
        self.role_channels={**ROLE_CHANNEL,'Immutable Pulse':7,'Loop Drums':9,
                           'Memory Plucks':5,'Slow Upper Voices':0,'Expressive Bass':1,'Companion Guitar':3}

    def _emotion(self,bar):
        p=(bar+.5)/self.total_bars
        index=min(len(self.arc)-1,int(p*len(self.arc)))
        return self.arc[index], EMOTIONS[self.arc[index]]

    def _add(self,role,pitch,bar,beat,duration,velocity):
        self._emit(role,pitch,bar,beat,duration,velocity)

    def compose(self):
        # Generate a loop-first composition. The anchor and drums are explicitly immune to expressive modification.
        tones=MODES[self.mode]
        root=self.low_note
        synth_notes=[root+24+tones[x] for x in (4,2,1,0)]
        for bar in range(self.total_bars):
            emotion, state=self._emotion(bar)
            if bar%max(1,self.total_bars//len(self.arc))==0:
                self.emotional_log.append({'bar':bar+1,'emotion':emotion,'state':state})
            if self.anchor!='none':
                # Identical 2-bar anchor regardless of harmonic-emotional state.
                for beat,offset,dur,vel in self.anchor_pattern:
                    self._add('Immutable Pulse',root+(12 if self.anchor=='synth' else 0)+offset,bar,beat,dur,vel)
            # Frozen two-bar drums: no rests or fills, no velocity/timing mutation.
            for beat,pitch,vel,dur in self.drum_pattern:
                self._add('Loop Drums',pitch,bar,beat,dur,vel)
            # Harmonic shift is slow; no functional progressions. Retain common tones on stationary pedal.
            phase=bar//max(8,self.total_bars//(len(self.arc)*2))
            harmony=[root+24,root+27,root+31,root+38]
            if emotion in ('acceptance','triumph'):
                harmony=[root+24,root+27,root+33,root+38]  # sixth reinterprets root pedal
            elif emotion=='unease':
                harmony=[root+24,root+25,root+31,root+38]
            elif emotion=='numbness':
                harmony=[root+24,root+29,root+31]
            if bar%4==0:
                # Add notes sparsely and use changing upper pitch color only.
                for i,n in enumerate(harmony[1:]):
                    self._add('Slow Upper Voices',n,bar,0, min(14.8,4*(4 if self.repetition!='immutable' else 2)-.15),
                              max(34,52+state['velocity']-i*3))
            # A recognizable four-note group returns every four bars. Phase moves different roles against each other.
            if bar%4==0:
                shift=(bar//4)%5*.125 if self.repetition=='phase' else 0
                for i,(p,n) in enumerate(zip((.5,1.375,2.375,3.25),synth_notes)):
                    if self.repetition=='microevolution' and emotion=='numbness' and i==3:continue
                    p=p+shift
                    p=p if p<3.95 else p-1
                    self._add('Memory Plucks',n+(12 if emotion=='triumph' and i==0 else 0),bar,p,
                              [.34,.44,.37,.6][i],54+state['velocity'])
            # Expressive bass is deliberately optional in immutable mode to avoid disrupting the pedal.
            if self.repetition!='immutable' and bar%2==0 and state['density']>.4:
                for j,(b,interval) in enumerate(((0,0),(2.5,7),(3.5,5))):
                    self._add('Expressive Bass',root+12+interval,bar,b,.75 if j==0 else .40,72+state['velocity']-j*5)
            if self.repetition=='phase' and bar%3==0:
                self._add('Companion Guitar',root+36+tones[2],bar,.25,.34,51+state['velocity'])
            if self.repetition=='microevolution' and bar%8==7 and emotion in ('acceptance','triumph'):
                self._add('Companion Guitar',root+36+tones[4],bar,3.0,.72,47)
        return self

    def _expressive_performance(self):
        # Deterministic, phrase-aware velocities/attacks/gates. Locked tracks are never touched.
        rng=random.Random(self.seed+4040)
        if self.instrument_detail=='machine':return
        for role in ('Memory Plucks','Expressive Bass','Companion Guitar','Slow Upper Voices'):
            new=[]
            for start,n,d,v in self.events[role]:
                beat=(start//PPQ)%4
                bar=start//(4*PPQ)
                accent=6 if beat==0 else 3 if beat==2 else -2
                phrase=3 if bar%8==0 else -3 if bar%8==7 else 0
                # not indiscriminate velocity randomization
                if role=='Expressive Bass':
                    is_root=(n%12)==(self.low_note%12)
                    v+=accent+phrase+(7 if is_root else -5)
                    d=int(d*(.91 if not is_root else .98))
                    shift=3 if beat in (1,3) else 0
                elif role=='Companion Guitar':
                    v+=accent-5+phrase
                    d=int(d*.78)
                    shift=4 if self.instrument_detail=='expressive' else 1
                elif role=='Slow Upper Voices':
                    v+=(-4 if n<65 else 2)+phrase
                    shift=0
                else:
                    v+=accent+phrase+(3 if (n%12) in (2,6,9) else -3)
                    shift=2 if self.instrument_detail=='expressive' else 0
                new.append((max(0,start+shift),n,max(2,d),max(1,min(127,v))))
            self.events[role]=new

    def write_v4(self,out):
        self._expressive_performance()
        # Work with v3 native writer, mapping new roles onto the known channel structure by direct temporary role map patch.
        from midilab3 import ROLE_CHANNEL as channels
        saved=channels.copy()
        channels.update({k:v for k,v in self.role_channels.items() if k not in channels})
        try:
            path,mp=super().write(Path(out))
        finally:
            channels.clear();channels.update(saved)
        data=json.loads(mp.read_text())
        data.update({'schema':'MIDI_LAB_4.0','emotional_arc':self.arc,'emotional_log':self.emotional_log,
                     'repetition_mode':self.repetition,'drums_immutable':True,
                     'anchor_immutable':self.anchor!='none','instrument_detail':self.instrument_detail,
                     'max_active_roles':5,'performance_locked_tracks':['Immutable Pulse','Loop Drums']})
        mp.write_text(json.dumps(data,indent=2))
        return path,mp


def extract_patterns(path,track_name,loop_bars=2):
    mid=MidiFile(path); result=[]
    for tr in mid.tracks:
        name=next((m.name for m in tr if m.is_meta and m.type=='track_name'),'')
        if name!=track_name:continue
        absolute=0;events=[]
        for m in tr:
            absolute+=m.time
            if not m.is_meta and m.type in ('note_on','note_off'):
                events.append((absolute,m.type,m.note,m.velocity,m.channel))
        tpb=mid.ticks_per_beat; span=loop_bars*4*tpb
        bars=max((e[0] for e in events),default=0)//(4*tpb)+1
        cycles=math.ceil(bars/loop_bars)
        for i in range(cycles):
            result.append(tuple((t-i*span,k,n,v,c) for t,k,n,v,c in events if i*span<=t<(i+1)*span))
        return result
    raise ValueError(f'Track absent: {track_name}')

def exact_loop_test(path,name,expected_cycles):
    patterns=extract_patterns(path,name)
    assert len(patterns)==expected_cycles,(name,len(patterns),expected_cycles)
    assert len(set(patterns))==1,f'{name} changes across cycles'
    return {'track':name,'cycles':len(patterns),'identical':True,'events_per_cycle':len(patterns[0])}

def cook(args):
    common=dict(bpm=args.bpm,minutes=args.minutes,key=args.key,mode=args.mode,profile=args.profile,
                harmony=args.harmony,rhythm=args.rhythm,bass=args.bass,melody=args.melody,
                arrangement=args.arrangement,drums=args.drums,mood=args.mood,seed=args.seed,
                variant=args.variant,feel='none',weirdness=tuple(map(int,args.weirdness.split(','))))
    comp=ComposerV4(**common,emotional_arc=args.arc,repetition=args.repetition,
                    anchor=args.anchor,instrument_detail=args.instrument_detail).compose()
    path,mp=comp.write_v4(args.output)
    cycles=comp.total_bars//2
    if comp.total_bars%2:raise ValueError('Use even number of bars for the exact two-bar-lock guarantee')
    locks=[exact_loop_test(path,'Loop Drums',cycles)]
    if args.anchor!='none':locks.append(exact_loop_test(path,'Immutable Pulse',cycles))
    result=analyze(path,mp)
    if not result['technical_pass']:raise RuntimeError(f'Failed integrity test: {result["validation"]}')
    ap=path.with_suffix('.audit.json');ap.write_text(json.dumps(result,indent=2))
    lp=path.with_suffix('.locks.json');lp.write_text(json.dumps(locks,indent=2))
    return {'midi':str(path),'manifest':str(mp),'audit':str(ap),'lock_report':str(lp),'bars':comp.total_bars,
            'minutes':round(comp.total_bars*4/comp.bpm,3),'emotions':comp.arc,'technical_pass':True}

def main():
    p=argparse.ArgumentParser(description='MIDI Lab v4.0: emotional architecture, repetition, performance')
    sub=p.add_subparsers(dest='cmd',required=True)
    c=sub.add_parser('cook')
    c.add_argument('--profile',default='yl_tender_nocturne')
    for axis in ('harmony','rhythm','bass','melody','arrangement'):c.add_argument('--'+axis)
    c.add_argument('--bpm',type=int,default=94);c.add_argument('--minutes',type=float,default=4)
    c.add_argument('--key',default='B');c.add_argument('--mode',choices=list(MODES),default='minor')
    c.add_argument('--drums',default='minimal');c.add_argument('--mood',default='tender')
    c.add_argument('--seed',type=int,default=42)
    c.add_argument('--variant',choices=('default','restrained','melodic','strange'),default='default')
    c.add_argument('--weirdness',default='3,4,2,2,4')
    c.add_argument('--arc',default='regret,numbness,recognition,acceptance,triumph')
    c.add_argument('--repetition',choices=('immutable','microevolution','phase'),default='microevolution')
    c.add_argument('--anchor',choices=('synth','bass','none'),default='synth')
    c.add_argument('--instrument-detail',choices=('machine','natural','expressive'),default='expressive')
    c.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.cmd=='cook':print(json.dumps(cook(a),indent=2))
if __name__=='__main__':main()
