#!/usr/bin/env python3
"""MIDI Lab 3.0 - musical-intelligence composer, reproducible and patch independent.

Built from earlier MIDI Lab profile library. Uses authored algorithms, not trained AI.
Requires: mido. Invoke `python midilab3.py cook --help`.
"""
from __future__ import annotations
import argparse, collections, json, math, random, shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo
from harmony3 import NAMES, MODES, Chord, degree_chord, normalize_key, section_chords, voice_lead, bass_root
from rhythm3 import ENGINES, infer_engine, render_bar
from fretboard3 import chord_shape, arpeggio

ROOT=Path(__file__).resolve().parent
PPQ=480
DRUM_CH=9
ROLE_CHANNEL={'Harmonic Bed':0,'Melodic Bass':1,'Sub Sequence':2,'Picked Guitar':3,
              'Reply Guitar':4,'Four Note Hook':5,'Ghost Keys':6,'Drum Engine':9}
SECTION_NAMES=('Signal','Verse / establish','Lift / question','Hook / release',
               'Open / fragile bridge','Second arrival','Final reinterpretation','Coda / residue')
SECTION_WEIGHTS=(.09,.17,.12,.18,.11,.12,.15,.06)
SECTION_ENERGY=(.20,.51,.66,.79,.24,.65,.86,.18)
DRUM_FAMILIES=('ballad','postpunk','motorik','ukg','jungle','eurodance','idm','minimal')

@dataclass
class Section:
    name:str
    start:int
    end:int
    energy:float

class ComposerV3:
    def __init__(self,bpm=123,minutes=3.25,key='A',mode='minor',profile='drums_solo_jonny',
                 harmony=None,rhythm=None,bass=None,melody=None,arrangement=None,
                 drums='auto',mood='auto',seed=42,variant='default',feel='natural',
                 weirdness=(3,4,2,2,4)):
        if not(40<=bpm<=220):raise ValueError('BPM must be 40..220')
        if not(.75<=minutes<=9):raise ValueError('Minutes must be .75..9')
        if mode not in MODES:raise ValueError(f'Unsupported mode: {mode}')
        if variant not in ('default','restrained','melodic','strange'):raise ValueError('Bad variant')
        if feel not in ('none','natural','tight','loose','neworder'):raise ValueError('Bad feel')
        if len(weirdness)!=5 or any(x<0 or x>10 for x in weirdness):raise ValueError('Weirdness must be five values, 0..10')
        self.profiles=json.loads((ROOT/'style_profiles.json').read_text(encoding='utf-8'))['profiles']
        self.approved_adjustments=json.loads((ROOT/'taste_ledger.json').read_text(encoding='utf-8')).get('approved_adjustments',{})
        self.assignments=dict(harmony=harmony or profile,rhythm=rhythm or profile,bass=bass or profile,
                              melody=melody or profile,arrangement=arrangement or profile)
        for x in self.assignments.values():
            if x not in self.profiles:raise ValueError(f'Unknown profile {x}. See style_profiles.json')
        self.key_pc=normalize_key(key);self.key=NAMES[self.key_pc];self.mode=mode
        self.bpm=bpm;self.minutes=minutes;self.seed=seed;self.rng=random.Random(seed)
        self.variant=variant;self.feel=feel;self.weirdness=tuple(weirdness)
        self.total_bars=int(round(minutes*bpm/4))
        self.sections=self._sections()
        self.drum_engine=infer_engine(self.assignments['rhythm']) if drums=='auto' else drums
        if self.drum_engine not in ENGINES:raise ValueError(f'Unknown drum engine: {drums}')
        self.mood=(self._infer_mood() if mood=='auto' else mood)
        if self.mood not in ('tender','driving','hazy','bright'):raise ValueError('Invalid mood')
        self.events={k:[] for k in ROLE_CHANNEL}
        self.prev_voicing=None;self.prev_grip=None
        self.chord_log=[];self.guitar_log=[];self.motif_log=[]
        self.use_sub=any(x in self.assignments['bass'] for x in ('no_technique','no_lowlife','no_republic','pink_liquid','pink_bedroom','ukg_elegant'))
        self.motif=self._motif()
        self.fretboard_fallbacks=0

    def _style(self,axis,feature):
        delta=self.approved_adjustments.get(feature,0)
        return max(0,min(10,self.profiles[self.assignments[axis]]['engine'][feature]+delta))

    def _infer_mood(self):
        h=self.assignments['harmony'].lower()
        if any(w in h for w in ('haze','nocturne','casio','afterhours','parttime_lies')):return 'hazy'
        if any(w in h for w in ('technique','lcd','eurodance','neon','motorik')):return 'driving'
        if any(w in h for w in ('pcl','republic','fancy')):return 'bright'
        return 'tender'

    def _sections(self):
        total=self.total_bars
        # Allocate nearly all sections on 2-bar boundaries, with last section consuming remainder.
        weights=list(SECTION_WEIGHTS)
        if self.weirdness[2]>=7: # unusual form: longer fragile middle, shorter second arrival
            weights[4]+=.055; weights[5]-=.055
        lengths=[max(4,2*round(total*w/2)) for w in weights[:-1]]
        while sum(lengths)>total-4:
            i=max(range(len(lengths)),key=lambda j:lengths[j])
            lengths[i]-=2
        lengths.append(total-sum(lengths))
        result=[];pos=0
        for i,(name,le,en) in enumerate(zip(SECTION_NAMES,lengths,SECTION_ENERGY)):
            result.append(Section(name,pos,pos+le,en));pos+=le
        assert pos==total
        return result

    def _motif(self):
        scale=MODES[self.mode]
        # Four-note interval identity, original to this generator. Choose contour from modal degrees.
        base=60+self.key_pc
        if base<65:base+=12
        if base>72:base-=12
        choices=([4,3,1,0],[4,2,1,0],[2,3,1,0]) if self.mood in ('tender','hazy') else ([2,4,3,0],[4,2,3,0])
        degrees=list(self.rng.choice(choices))
        notes=[base+scale[i] for i in degrees]
        return {'pitches':notes, 'degrees':degrees, 'intervals':[notes[i+1]-notes[i] for i in range(3)],
                'rhythm':[.5,1.25,2.25,3.25],
                'final_operation':'reverse order, delay final note and reharmonize with a borrowed chord'}

    def _emit(self,role,note,bar,beat,dur,vel,articulation=None):
        if not (0<=note<=127):return
        start=int(round((bar*4+beat)*PPQ))
        if start<0:return
        d=max(2,int(round(dur*PPQ)))
        self.events[role].append((start,int(note),d,int(max(1,min(127,vel)))))

    def _make_chord(self,bar,section_index):
        s=self.sections[section_index]
        i=(bar-s.start)%8
        chord=section_chords(self.key_pc,self.mode,self.mood,section_index)[i]
        if self.weirdness[0]>=7 and section_index in (2,5) and bar%16==15:
            chord=degree_chord(self.key_pc,self.mode,4,borrowed=True)
        # Extended color created from modal scale: substitute the 9th for the 5th.
        if not chord.borrowed and self.mood in ('hazy','tender') and bar%4==1:
            pc9=(self.key_pc+MODES[self.mode][chord.degree%7])%12
            if pc9 not in chord.pcs:
                chord=Chord(chord.degree,chord.root_pc,(chord.pcs[0],chord.pcs[1],chord.pcs[3],pc9),chord.symbol+' add9',False)
        return chord

    def _chords(self,bar,si,chord):
        energy=self.sections[si].energy
        v=voice_lead(chord,self.prev_voicing)
        self.prev_voicing=v
        dur=3.65 if si in (0,4,7) or self.mood=='hazy' else (1.5 if self.drum_engine=='eurodance' else 3.2)
        velocity=53+int(energy*17)
        if self.variant=='restrained':velocity-=7
        for j,p in enumerate(v):self._emit('Harmonic Bed',p,bar,j*.008,dur,velocity-j*3)
        if si in (3,6) and bar%4==2 and self.drum_engine in ('ukg','eurodance','motorik') and self.variant!='restrained':
            for j,p in enumerate(v[1:-1]):self._emit('Harmonic Bed',p,bar,2.5+j*.01,.34,velocity-11)
        self.chord_log.append({'bar':bar+1,'symbol':chord.symbol,'pitches':v,'borrowed':chord.borrowed})

    def _bass(self,bar,si,chord):
        if si==0:return
        root=bass_root(chord)
        energy=self.sections[si].energy
        motion=self._style('bass','bass_motion')
        # Different rhythmic cells selected by bass motion and groove family.
        if self.drum_engine in ('ukg','jungle'):
            pattern=[(0,0,.65,88),(1.5,7,.27,66),(2.75,12,.42,74),(3.5,5,.25,62)]
        elif self.drum_engine in ('motorik','eurodance'):
            pattern=[(0,12,.45,87),(.75,7,.31,76),(2,12,.43,82),(3,5,.41,72)]
        elif self.drum_engine=='ballad':
            pattern=[(0,12,1.05,79),(2.5,7,.66,68),(3.5,5,.34,59)]
        else:
            pattern=[(0,12,.63,84),(1.25,7,.42,70),(2.5,4,.39,73),(3.5,12,.24,65)]
        if motion<=4:pattern=pattern[::2]
        if motion>=8 and si in (2,3,6) and bar%4==3:
            pattern.append((3.75,11,.20,59))
        if si==4:pattern=pattern[:2]
        if si==7:pattern=pattern[:2]
        if self.variant=='restrained':pattern=pattern[:max(1,len(pattern)-1)]
        # Root+4 is made diatonic to the active chord if necessary.
        chord_pcs=set(chord.pcs)
        for p,interval,d,v in pattern:
            n=root+interval
            if n%12 not in chord_pcs:
                candidates=[x for x in range(n-3,n+4) if x%12 in chord_pcs]
                if candidates:n=min(candidates,key=lambda x:abs(x-n))
            self._emit('Melodic Bass',n,bar,p,d,v)
        if self.use_sub and si not in (0,4,7):
            sub_positions=[(0,.71,85),(2,.5,69)] if self.drum_engine!='ukg' else [(0,.6,86),(2.5,.38,74)]
            for p,d,v in sub_positions:self._emit('Sub Sequence',root,bar,p,d,v)

    def _guitar(self,bar,si,chord,lead_active):
        # Physically realizable frets/strings for each harmonic chord.
        grip=chord_shape(chord.pcs, self.prev_grip)
        if grip is None:
            self.fretboard_fallbacks+=1
            return
        self.prev_grip=grip
        if bar%4==0:self.guitar_log.append({'bar':bar+1,'grip':[(i+1,f,p) for i,f,p in grip],'chord':chord.symbol})
        activity=self._style('arrangement','guitar_activity')
        density=('sparse' if (si in (0,4,7) or lead_active or self.variant=='restrained') else 'full' if activity>=8 else 'medium')
        for p,n,d,v in arpeggio(grip,bar,density):
            if si==0 and p<1.0 and bar%2!=0:continue
            self._emit('Picked Guitar',n,bar,p,d,v)
        # Second guitar is not a second full strum; it replies in holes.
        if si in (2,5) and activity>=6 and self._style('arrangement','arrangement_growth')>=5 and self.variant!='restrained' and bar%2==1:
            pitch=grip[-1][2]
            self._emit('Reply Guitar',pitch,bar,2.75,.58,53)

    def _lead(self,bar,si,chord):
        if si not in (2,3,5,6):return
        s=self.sections[si]
        local=bar-s.start
        if local%4 not in (0,2):return  # instrumental space for vocals
        if self._style('melody','hook_density')<=4 and local%4==2:return
        pitches=self.motif['pitches'][:]
        rhythm=self.motif['rhythm'][:]
        operation='original'
        if si==2:
            pitches=pitches[:3];rhythm=rhythm[:3];operation='fragment'
        elif si==5:
            rhythm=[x+.125 for x in rhythm];operation='anticipation and displacement'
        elif si==6:
            pitches=[pitches[3],pitches[1],pitches[2],pitches[0]]
            rhythm=[.25,1.5,2.5,3.375]
            operation='reordered contour, delayed ending / new harmony'
        elif local%4==2:
            pitches[-1]=pitches[-1]+2 if pitches[-1]+2<=84 else pitches[-1]-2
            operation='changed final note'
        if self.weirdness[3]>=7 and si==6 and local%4==2:
            pitches[1]+=12
            operation+='; octave flare'
        if self.variant=='strange' and si in (3,6):
            rhythm=[min(3.625,p+(.125 if j%2==1 else 0)) for j,p in enumerate(rhythm)]
            operation+='; controlled rhythmic shift'
        if self.variant=='melodic' and si==3 and local%4==0:
            pitches+=[pitches[-2]];rhythm+=[3.875]
        if self.variant=='restrained':
            pitches=pitches[:3];rhythm=rhythm[:3]
        for i,(p,n) in enumerate(zip(rhythm,pitches)):
            self._emit('Four Note Hook',n,bar,p,(.48 if i<3 else .60),68+(10 if i==0 else 0))
        self.motif_log.append({'bar':bar+1,'operation':operation,'notes':pitches})

    def _ghost(self,bar,si,chord):
        art=self._style('arrangement','synthetic_artifacts')
        if (art+self.weirdness[4]//3)<4 or self.variant=='restrained' or si in (4,7):return
        if bar%4==3:
            note=72+self.key_pc
            while note>84:note-=12
            self._emit('Ghost Keys',note,bar,3.25,.36,37)
        if si==6 and art>=7 and bar%8==6:
            self._emit('Ghost Keys',67+self.key_pc,bar,1.75,.16,47)

    def _drums(self,bar,si):
        s=self.sections[si]
        if si in (0,4):return
        energy=s.energy
        if si==7:energy=.24
        mut=min(10,self._style('rhythm','drum_mutation')+self.weirdness[1]//3)
        if self.variant=='strange':mut=min(10,mut+3)
        swing=.12 if self.drum_engine=='ukg' else 0
        fill=(bar==s.end-1)
        events=render_bar(self.drum_engine,bar,energy,mut,fill,swing)
        if self.variant=='restrained':
            events=[x for x in events if x[1] not in (37,45,70) and (x[1]!=42 or int(x[0]*2)%2==0)]
        for p,n,v,d in events:self._emit('Drum Engine',n,bar,p,d,v)

    def compose(self):
        for si,s in enumerate(self.sections):
            for bar in range(s.start,s.end):
                chord=self._make_chord(bar,si)
                self._chords(bar,si,chord)
                if si!=0:self._bass(bar,si,chord)
                self._guitar(bar,si,chord,si in (2,3,6))
                self._lead(bar,si,chord)
                self._ghost(bar,si,chord)
                self._drums(bar,si)
        if self.variant=='strange':
            # Preserve hook but remove some accompaniment in the final reinterpretation.
            s=self.sections[6]
            lo=s.start*4*PPQ;hi=s.end*4*PPQ
            self.events['Picked Guitar']=[x for x in self.events['Picked Guitar'] if not(lo<=x[0]<hi and (x[0]//(4*PPQ))%4==2)]
        return self

    def _meta_key(self):
        # Use the diatonic relative major for modal key signatures.
        if self.mode=='dorian':name=NAMES[(self.key_pc+10)%12]
        elif self.mode=='mixolydian':name=NAMES[(self.key_pc+5)%12]
        else:name=self.key+('m' if self.mode=='minor' else '')
        try:MetaMessage('key_signature',key=name,time=0);return name
        except ValueError:return 'C'

    def write(self,out:Path):
        out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
        mid=MidiFile(type=1,ticks_per_beat=PPQ)
        c=MidiTrack();mid.tracks.append(c)
        c.append(MetaMessage('track_name',name='Conductor',time=0))
        c.append(MetaMessage('set_tempo',tempo=bpm2tempo(self.bpm),time=0))
        c.append(MetaMessage('time_signature',numerator=4,denominator=4,time=0))
        c.append(MetaMessage('key_signature',key=self._meta_key(),time=0))
        last=0
        for s in self.sections:
            t=s.start*4*PPQ
            c.append(MetaMessage('marker',text=s.name,time=t-last));last=t
        c.append(MetaMessage('end_of_track',time=self.total_bars*4*PPQ-last))
        for role,ch in ROLE_CHANNEL.items():
            notes=sorted(self.events[role],key=lambda x:(x[0],x[1]))
            if not notes:continue
            # Ensure no same-pitch/channel overlap that could stick notes in a DAW.
            slots=collections.defaultdict(list)
            for start,pitch,dur,vel in notes:slots[pitch].append([start,pitch,dur,vel])
            for group in slots.values():
                group.sort(key=lambda n:n[0])
                for one,two in zip(group,group[1:]):
                    if one[0]+one[2]>=two[0]:one[2]=max(1,two[0]-one[0]-1)
            events=[]
            for group in slots.values():
                for start,pitch,dur,vel in group:
                    events.append((start,1,Message('note_on',channel=ch,note=pitch,velocity=vel,time=0)))
                    events.append((start+dur,0,Message('note_off',channel=ch,note=pitch,velocity=0,time=0)))
            events.sort(key=lambda x:(x[0],x[1]))
            tr=MidiTrack();mid.tracks.append(tr)
            tr.append(MetaMessage('track_name',name=role,time=0))
            last=0
            for tick,_,msg in events:
                msg.time=tick-last;tr.append(msg);last=tick
            tr.append(MetaMessage('end_of_track',time=0))
        mid.save(out)
        manifest={
            'schema':'MIDI_LAB_3.0','generated':out.name,'bpm':self.bpm,
            'requested_minutes':self.minutes,'actual_minutes':round(self.total_bars*4/self.bpm,4),
            'key':self.key,'mode':self.mode,'ppq':PPQ,'bars':self.total_bars,'seed':self.seed,
            'style_assignments':self.assignments,'drum_engine':self.drum_engine,
            'harmony_mood':self.mood,'performance':self.feel,'variant':self.variant,
            'weirdness':dict(zip(('harmony','rhythm','form','register','texture'),self.weirdness)),
            'motif_ledger':self.motif,'motif_reappearances':self.motif_log,
            'harmonic_sequence':self.chord_log,'guitar_fretboard_grips':self.guitar_log,
            'guitar_shape_fallbacks':self.fretboard_fallbacks,
            'sections':[{'name':s.name,'start_bar':s.start+1,'end_bar':s.end,'energy':s.energy} for s in self.sections],
            'role_notes':{k:len(v) for k,v in self.events.items()},
            'limitations':['Rule-based MIDI composition, not audio rendering or a trained music model.',
                           'Guitar fretboard shapes assume standard tuning; actual patch may not support guitar articulations.',
                           'Key signature meta-events cannot express modal key signatures uniquely.',
                           'Velocity response varies by receiving Logic Pro instrument.']
        }
        mp=out.with_suffix('.manifest.json')
        mp.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        return out,mp

def process_cook(a):
    try:w=tuple(int(x) for x in a.weirdness.split(','))
    except ValueError:raise SystemExit('--weirdness must be five 0..10 integers separated by commas')
    c=ComposerV3(bpm=a.bpm,minutes=a.minutes,key=a.key,mode=a.mode,profile=a.profile,
                 harmony=a.harmony,rhythm=a.rhythm,bass=a.bass,melody=a.melody,
                 arrangement=a.arrangement,drums=a.drums,mood=a.mood,seed=a.seed,
                 variant=a.variant,feel=a.performance,weirdness=w).compose()
    outfile,manifest=c.write(a.output)
    if a.performance!='none':
        from performance import apply_performance
        tmp=outfile.with_name(outfile.stem+'.performance-temp.mid')
        perf=apply_performance(outfile,tmp,feel=a.performance,seed=a.seed)
        tmp.replace(outfile)
        perf['output']=str(outfile)
        outfile.with_suffix('.performance.json').write_text(json.dumps(perf,indent=2),encoding='utf-8')
    from analyze3 import analyze
    result=analyze(outfile,manifest)
    rp=outfile.with_suffix('.audit.json')
    rp.write_text(json.dumps(result,indent=2),encoding='utf-8')
    if not result['technical_pass']:
        raise RuntimeError('MIDI failed technical validation: '+str(result['validation']))
    return {'midi':str(outfile),'manifest':str(manifest),'audit':str(rp),
            'bpm':c.bpm,'bars':c.total_bars,'minutes':round(c.total_bars*4/c.bpm,3),
            'drum_engine':c.drum_engine,'key':c.key,'mode':c.mode,'technical_pass':True}

def main():
    p=argparse.ArgumentParser(description='MIDI Lab v3.0 Musical Intelligence')
    sub=p.add_subparsers(dest='command',required=True)
    cook=sub.add_parser('cook',help='Generate a new patch-independent multitrack MIDI')
    cook.add_argument('--profile',default='drums_solo_jonny')
    for axis in ('harmony','rhythm','bass','melody','arrangement'):cook.add_argument('--'+axis,default=None)
    cook.add_argument('--bpm',type=int,default=123)
    cook.add_argument('--minutes',type=float,default=3.25)
    cook.add_argument('--key',default='A',help='Tonic C, C#, D, Eb, ... Bb, B')
    cook.add_argument('--mode',choices=list(MODES),default='minor')
    cook.add_argument('--drums',choices=['auto',*ENGINES],default='auto')
    cook.add_argument('--mood',choices=['auto','tender','driving','hazy','bright'],default='auto')
    cook.add_argument('--seed',type=int,default=42)
    cook.add_argument('--variant',choices=['default','restrained','melodic','strange'],default='default')
    cook.add_argument('--performance',choices=['none','natural','tight','loose','neworder'],default='natural')
    cook.add_argument('--weirdness',default='3,4,2,2,4')
    cook.add_argument('--output',type=Path,default=ROOT/'examples'/'midilab3_demo.mid')
    analyze_p=sub.add_parser('analyze',help='Inspect any MIDI including pre-v3 files')
    analyze_p.add_argument('--input',type=Path,required=True)
    analyze_p.add_argument('--manifest',type=Path,default=None)
    analyze_p.add_argument('--output',type=Path,default=None)
    compare_p=sub.add_parser('compare',help='Compare two MIDI files via measurable features')
    compare_p.add_argument('--a',type=Path,required=True);compare_p.add_argument('--b',type=Path,required=True)
    compare_p.add_argument('--output',type=Path,default=None)
    sub.add_parser('profiles',help='Print all available taste profile identifiers')
    fb=sub.add_parser('feedback',help='Record listening feedback in the local taste ledger; no automatic retraining')
    fb.add_argument('--track',required=True)
    fb.add_argument('--part',default='whole track')
    fb.add_argument('--rating',required=True,type=int,choices=(1,2,3,4,5))
    fb.add_argument('--note',required=True)
    fb.add_argument('--tags',default='')
    approve=sub.add_parser('approve-adjustment',help='Explicitly approve a small house-preference numeric adjustment')
    approve.add_argument('--parameter',choices=('bass_motion','drum_mutation','guitar_activity','synthetic_artifacts','hook_density','arrangement_growth','harmonic_borrow'),required=True)
    approve.add_argument('--delta',type=int,required=True,choices=range(-3,4))
    args=p.parse_args()
    if args.command=='cook':
        print(json.dumps(process_cook(args),indent=2))
    elif args.command=='analyze':
        from analyze3 import analyze
        result=analyze(args.input,args.manifest)
        if args.output:args.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result,indent=2))
    elif args.command=='compare':
        from analyze3 import compare
        result=compare(args.a,args.b)
        if args.output:args.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result,indent=2))
    elif args.command=='profiles':
        profiles=json.loads((ROOT/'style_profiles.json').read_text())['profiles']
        for name in sorted(profiles):print(name)
    elif args.command in ('feedback','approve-adjustment'):
        ledger_path=ROOT/'taste_ledger.json'
        ledger=json.loads(ledger_path.read_text(encoding='utf-8'))
        if args.command=='feedback':
            ledger.setdefault('feedback',[]).append({'track':args.track,'part':args.part,
                'rating':args.rating,'note':args.note,'tags':[x.strip() for x in args.tags.split(',') if x.strip()]})
            message='Feedback recorded; house weights unchanged.'
        else:
            adj=ledger.setdefault('approved_adjustments',{})
            adj[args.parameter]=args.delta
            message=f'Approved adjustment: {args.parameter}={args.delta}'
        ledger_path.write_text(json.dumps(ledger,indent=2),encoding='utf-8')
        print(message)
if __name__=='__main__':main()
