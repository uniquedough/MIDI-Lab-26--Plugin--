#!/usr/bin/env python3
"""MIDI Lab v2 - deterministic original composition, quality analysis, taste logging.
Requires: pip install mido. No network or API needed.

Commands:
  cook, variant, analyze, audit, benchmark, feedback

Design note: genre profiles are high-level composition traits, not transcriptions.
"""
from __future__ import annotations
import argparse, collections, copy, json, math, random, statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo

ROOT = Path(__file__).resolve().parent
PPQ = 480
PITCH_CLASSES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
GM_DRUMS = dict(kick=36, snare=38, rim=37, closed_hat=42, open_hat=46, low_tom=45)

@dataclass(frozen=True)
class Section:
    name: str
    start: int
    end: int
    energy: float
    roles: tuple[str, ...]

SECTION_TEMPLATE = [
    ('SIGNAL / half remembered',8,.22,('chords','ghost')),
    ('LOCK / uncertain sunlight',16,.45,('chords','bass','drums','guitar_a')),
    ('EXPAND / anticipation',8,.60,('chords','bass','drums','guitar_a','guitar_b')),
    ('HOOK / pretty discomfort',16,.78,('chords','bass','drums','guitar_a','lead')),
    ('RETURN / too much to say',16,.66,('chords','bass','drums','guitar_a','guitar_b','lead')),
    ('OPEN / missing frame',8,.37,('chords','bass','ghost')),
    ('BLOOM / lights in the street',16,.96,('chords','bass','drums','guitar_a','guitar_b','lead','ghost')),
    ('RESIDUE / last bus',12,.25,('chords','bass','ghost')),
]

# Named harmony - purposely distinguish full chords from independent bass roots.
A_MAJOR = [
    dict(symbol='Aadd9',root=33,notes=(57,61,64,71),scale=(57,59,61,64,66,69,71,73,76)),
    dict(symbol='E/G#',root=32,notes=(56,59,64,68),scale=(56,59,61,64,68,71,73,76)),
    dict(symbol='F#m7',root=30,notes=(54,57,61,64),scale=(54,57,59,61,64,66,69,73)),
    dict(symbol='Dmaj9',root=38,notes=(50,54,57,61,64),scale=(54,57,59,61,64,66,69,73)),
]
BRIDGE = [
    dict(symbol='Bm7',root=35,notes=(47,50,54,57),scale=(57,59,62,66,69,71,74)),
    dict(symbol='Eadd9',root=40,notes=(52,56,59,66),scale=(56,59,61,64,66,68,71,73)),
    dict(symbol='Dm6 (borrowed iv)',root=38,notes=(50,53,57,59),scale=(53,57,59,62,65,69,74)),
    dict(symbol='Esus4',root=40,notes=(52,57,59,64),scale=(57,59,64,66,71,73)),
]

PERFORMERS = {
    'chords': dict(timing=3, velocity=5, duration=.95),
    'bass': dict(timing=4, velocity=7, duration=.92),
    'sub_bass': dict(timing=0, velocity=2, duration=.91),
    'guitar_a': dict(timing=6, velocity=8, duration=.81),
    'guitar_b': dict(timing=5, velocity=8, duration=.81),
    'lead': dict(timing=7, velocity=7, duration=.91),
    'ghost': dict(timing=9, velocity=12, duration=1.05),
    'drums': dict(timing=1, velocity=5, duration=1.00),
}

class Composer:
    def __init__(self, profile: str, bpm: int, minutes: float, seed: int, variant: str,
                 assignments: dict|None=None, weirdness: tuple[int,...]=(3,4,2,2,4)):
        self.bpm, self.minutes, self.seed, self.variant = bpm, minutes, seed, variant
        self.profile_id = profile
        profiles = json.loads((ROOT/'style_profiles.json').read_text())['profiles']
        if profile not in profiles:
            raise ValueError('Unknown profile. Available: ' + ', '.join(profiles))
        self.profile = profiles[profile]
        self.profiles = profiles
        self.assignments = {role:profile for role in ('harmony','rhythm','bass','melody','arrangement')}
        if assignments:
            for role, selected in assignments.items():
                if selected not in profiles: raise ValueError(f'Unknown profile for {role}: {selected}')
                self.assignments[role]=selected
        if len(weirdness)!=5 or any(not(0<=x<=10) for x in weirdness):
            raise ValueError('Weirdness must be five 0–10 numbers: harmonic,rhythmic,form,register,texture')
        self.weirdness = (tuple(min(10,v+boost) for v,boost in zip(weirdness,(1,3,0,2,3)))
                          if variant=='strange' else weirdness)
        ledger=json.loads((ROOT/'taste_ledger.json').read_text())
        self.approved_adjustments=ledger.get('approved_adjustments',{})
        self.rng = random.Random(seed)
        self.total_bars = max(32, int(round(minutes * bpm / 16))*4)
        self.sections = self._make_sections(self.total_bars)
        self.events: dict[str,list] = {role:[] for role in PERFORMERS}
        self.chord_history: list[tuple[int,...]] = []
        self.motif_ledger = self._make_ledger()
        self.track_channels = dict(chords=1,bass=2,guitar_a=3,guitar_b=4,lead=5,ghost=6,drums=9,sub_bass=7)

    def style(self, role, parameter):
        value = self.profiles[self.assignments[role]]['engine'][parameter]
        return max(0,min(10,value + self.approved_adjustments.get(parameter,0)))

    def _make_sections(self, bars):
        lengths = [max(4,round(bars*weight/100/4)*4) for _,weight,_,_ in SECTION_TEMPLATE]
        if self.weirdness[2]>=7 and lengths[4]>=12:
            lengths[4]-=4
            lengths[5]+=4  # an unusually long quiet middle; still exactly the same runtime
        delta=bars-sum(lengths)
        # Prefer modifying the outro and the longest middle sections.
        while delta:
            step=4 if delta>0 else -4
            indices = [7,4,3,1,6,2,5,0]
            for i in indices:
                if lengths[i]+step >= 4:
                    lengths[i]+=step; delta-=step; break
            else: raise ValueError('Could not allocate sections')
        out=[]; cursor=0
        for (name,_,energy,roles), length in zip(SECTION_TEMPLATE,lengths):
            out.append(Section(name,cursor,cursor+length,energy,roles))
            cursor+=length
        return out

    def _make_ledger(self):
        # Explicit reusable motif objects with named transformations.
        return {
            'M1 / wistful hook': {'intervals':[0,-2,3,-1,-4], 'rhythm':[.5,1.25,2.0,2.75,3.5],
                                  'operations':['fragment','ending_change','rhythmic_displacement','octave_echo']},
            'M2 / climbing interlock': {'degrees':[0,2,4,2], 'rhythm':[.25,1.5,2.25,3.25],
                                       'operations':['negative_space','register_swap','call_answer']},
            'R1 / stuttering machine': {'hat_eighths':True,'ghost_16th_positions':[1.75,3.75],
                                       'operations':['deletion','syncopated_pickup','half_time']},
            'H1 / daylight with a bruise': {'base':['Aadd9','E/G#','F#m7','Dmaj9'],
                                           'contrast':['Bm7','Eadd9','Dm6','Esus4'],
                                           'operations':['borrowed_minor_iv','pedal_common_tones','close_voice_leading']},
            'X1 / missing beat': {'behavior':'remove the drum and upper guitar parts for the OPEN section before BLOOM'}
        }

    def beat(self, bar, sub=0): return round((bar*4+sub)*PPQ)

    def section(self, bar):
        for i,s in enumerate(self.sections):
            if s.start<=bar<s.end: return i,s
        return 7,self.sections[-1]

    def chord(self, bar):
        idx,s=self.section(bar)
        if idx==5: return BRIDGE[(bar-s.start)%4]
        if idx==6 and bar in (s.start+8,s.start+9): return BRIDGE[2] # borrowed minor-IV moment
        if self.style('harmony','harmonic_borrow')+self.weirdness[0]>=14 and bar%16==15:
            return BRIDGE[2]
        return A_MAJOR[bar%4]

    def density(self, section_index):
        d=[.25,.50,.65,.79,.77,.28,.98,.23][section_index]
        growth=self.style('arrangement','arrangement_growth')
        if section_index in (3,6):d+=.02*(growth-5)
        return d * {'restrained':.64,'melodic':.92,'strange':.94,'default':1.0}[self.variant]

    def emit(self, role, pitch, bar, pos, dur, velocity):
        pr=PERFORMERS[role]
        if self.variant=='restrained':
            if role in ('ghost','guitar_b') and self.rng.random()<.67:return
            if role in ('guitar_a','lead') and self.rng.random()<.27:return
            if role=='drums' and pitch in (GM_DRUMS['closed_hat'],GM_DRUMS['rim']) and self.rng.random()<.23:return
        start=self.beat(bar,pos)+self.rng.randint(-pr['timing'],pr['timing'])
        start=max(0,start)
        dur=max(1,round(dur*PPQ*pr['duration']))
        vel=max(1,min(127,velocity+self.rng.randint(-pr['velocity'],pr['velocity'])))
        self.events[role].append((start,max(0,min(127,pitch)),dur,vel))

    @staticmethod
    def voice_lead(previous, pitches):
        if not previous:
            return tuple(pitches)
        # Preserve chord pitch-classes and pick a close placement in 48–72.
        result=[]
        for i,p in enumerate(pitches):
            choices=[p+shift for shift in (-12,0,12) if 47<=p+shift<=74]
            if not choices: choices=[p]
            ref=previous[min(i,len(previous)-1)]
            best=min(choices,key=lambda n:(abs(n-ref), abs(n-60)))
            result.append(best)
        # register monotonicity, don't permit excessive doubling from voice compression
        result.sort()
        return tuple(result)

    def compose(self):
        last_voicing=None
        for bar in range(self.total_bars):
            si,s=self.section(bar)
            chord=self.chord(bar)
            density=self.density(si)
            if 'chords' in s.roles:
                voiced=self.voice_lead(last_voicing,chord['notes'])
                last_voicing=voiced
                self.chord_history.append(voiced)
                # Soft clipped chords in early sections, suspended notes in open section.
                chord_duration=3.65 if si in (0,5,7) else 1.55
                chord_vel=47+int(s.energy*24)
                for n in voiced:
                    self.emit('chords',n,bar,0,chord_duration,chord_vel)
                if si in (3,6) and bar%2==0:
                    # Second stab only when lead/bass arrangement leaves space
                    for n in voiced[1:-1]:
                        self.emit('chords',n,bar,2.75,.39,chord_vel-6)
            if 'bass' in s.roles:
                self.bass(bar,si,chord,density)
                if self.assignments['bass'] in ('no_lowlife_machine_romance','no_technique_balearic','no_republic_afterglow'):
                    self.sub_bass(bar,si,chord)
            if 'guitar_a' in s.roles and (self.style('arrangement','guitar_activity')>=5 or si!=3):
                self.guitar_a(bar,si,chord,density)
            if 'guitar_b' in s.roles and self.style('arrangement','guitar_activity')>=4:
                self.guitar_b(bar,si,chord,density)
            if 'lead' in s.roles:
                self.lead(bar,si,chord,density)
            if 'ghost' in s.roles and self.style('arrangement','synthetic_artifacts')>=3:
                self.ghost(bar,si,chord,density)
            if 'drums' in s.roles:
                self.drums(bar,si,density)
        return self

    def bass(self,bar,si,chord,density):
        root=chord['root']
        # For the New Order dual-bass palette, reserve high register for picked bass.
        # A separately sequenced low register is composed by sub_bass().
        if self.assignments['bass'] in ('no_lowlife_machine_romance','no_technique_balearic','no_republic_afterglow'):
            self.hook_bass(bar,si,chord)
            return
        # Bass gets rhythmic agency: anticipations and octave shapes, not four root quarters.
        if si in (1,7): pattern=[(0,root+12,.69,79),(2.5,root+19,.39,64)]
        elif si==5: pattern=[(0,root+12,1.45,77),(2.5,root+19,.6,66)]
        else:
            pattern=[(0,root+12,.57,88),(.75,root+19,.3,67),
                     (1.5,root+24,.42,77),(2.75,root+16,.32,70),
                     (3.5,root+19,.24,65)]
            if bar%4==3: pattern[-1]=(3.5,root+11,.26,74)
        motion=self.style('bass','bass_motion')
        if motion<=5:pattern=[p for i,p in enumerate(pattern) if i in (0,2)]
        elif motion>=9 and si in (3,6) and bar%4==2:
            pattern.append((3.75,root+12,.11,61))
        if self.variant=='restrained':pattern=[p for i,p in enumerate(pattern) if i in (0,2,4)]
        for pos,n,d,vel in pattern:self.emit('bass',n,bar,pos,d,vel)

    def hook_bass(self,bar,si,chord):
        """Melodic picked mid/high bass; independently active over mono low-sequencer."""
        root=chord['root']
        # Root +24: A3 etc. Pitch choices avoid duplicating the sequenced root.
        shapes=[
            [(0.,24,.48,100),(1.,31,.35,77),(1.75,28,.48,87),(3.,26,.43,83)],
            [(.5,31,.32,83),(1.25,24,.52,98),(2.25,28,.45,85),(3.5,33,.22,72)],
            [(0.,24,.58,102),(1.5,26,.39,76),(2.5,31,.40,88),(3.25,28,.35,80)],
            [(.25,28,.32,80),(1.0,31,.37,88),(2.0,24,.71,99),(3.5,26,.26,75)],
        ]
        seq=shapes[bar%4]
        if si in (1,7):seq=seq[:2]
        if si==5:seq=[(0.,24,1.2,78),(2.75,31,.48,66)]
        if si==6 and bar%4==3:seq=seq[:-1]+[(3.50,29,.28,77)]
        for pos,interval,dur,vel in seq:
            self.emit('bass',root+interval,bar,pos,dur,vel)

    def sub_bass(self,bar,si,chord):
        """Rigid lower bass ostinato for New Order electronic rhythm profiles."""
        r=chord['root']
        if si in (1,7):seq=[(0.,r,.80,83),(2.,r+12,.45,66)]
        elif si==5:seq=[(0.,r,1.35,76)]
        else:
            seq=[(0.,r,.65,92),(1.5,r,.34,75),(2.,r+12,.38,80),(3.5,r+7,.33,74)]
        for pos,n,dur,vel in seq:
            self.emit('sub_bass',n,bar,pos,dur,vel)

    def guitar_a(self,bar,si,chord,density):
        # Clipped mid-register arpeggio, non-competing with lead.
        notes=[n+12 if n<61 else n for n in chord['notes']]
        notes=sorted(notes)
        rhythm=[(.25,notes[0],.20),(1.5,notes[2],.17),(2.25,notes[-1],.19),(3.25,notes[1],.20)]
        if si in (3,6): rhythm=rhythm[:3]  # Orchestration: lead is foreground
        if bar%8==7:rhythm=rhythm[:-1]
        guitar_activity=self.style('arrangement','guitar_activity')
        if guitar_activity<=5:rhythm=rhythm[:2]
        if guitar_activity>=9 and si in (1,2,4) and bar%4==0:
            rhythm.append((3.75,notes[-2],.12))
        if self.variant=='strange' and bar%4==3:rhythm=[(p+.125,n,d) for p,n,d in rhythm]
        for i,(p,n,d) in enumerate(rhythm):self.emit('guitar_a',n,bar,p,d,64+(i==0)*7)

    def guitar_b(self,bar,si,chord,density):
        notes=sorted(chord['notes'])
        rhythm=[(1.0,notes[-2]+12,.18),(2.5,notes[1]+12,.22),(3.75,notes[2]+12,.12)]
        if si==4 and bar%4==1:rhythm=rhythm[:1]
        if si==6:rhythm=rhythm[:2] # final chorus leaves lead space
        if self.style('arrangement','guitar_activity')<=6:rhythm=rhythm[:1]
        for p,n,d in rhythm:self.emit('guitar_b',n,bar,p,d,57)

    def lead(self,bar,si,chord,density):
        # Consistent M1 contour, recurrences transformed instead of new random hooks.
        base=[73,71,76,73,69] # C# B E C# A, original contour and timing
        positions=self.motif_ledger['M1 / wistful hook']['rhythm']
        motif=list(zip(positions,base))
        if si==4:
            motif=[(p+.125,n) for p,n in motif[:-1]] # displacement + fragmentation
        if si==6:
            motif=[(p,n+(12 if j==2 and bar%8==2 else 0)) for j,(p,n) in enumerate(motif)]
            if bar%4==3: motif[-1]=(motif[-1][0],68) # bittersweet altered ending
        if bar%8 in (5,7): motif=motif[:3] # allow breathing space
        if self.style('melody','hook_density')<=5:motif=motif[:3]
        if self.style('melody','hook_density')>=9 and bar%4==0:motif.append((3.875,71))
        if self.weirdness[3]>=7 and bar%8==2:motif=[(p,n+(12 if i==2 else 0)) for i,(p,n) in enumerate(motif)]
        if self.variant=='restrained':motif=motif[:3]
        if self.variant=='melodic' and bar%4==0:motif.append((3.875,71))
        if self.variant=='strange' and bar%4==2: motif=[(p,n) for p,n in motif if p!=1.25]
        for i,(p,n) in enumerate(motif): self.emit('lead',n,bar,p,.27 if i!=2 else .43,70+(i==0)*7)

    def ghost(self,bar,si,chord,density):
        if self.style('arrangement','synthetic_artifacts') + self.weirdness[4]<7:return
        if bar%4!=3 and si!=0:return
        if bar%4==3:
            self.emit('ghost',80 if si in (0,7) else 78,bar,3.375,.34,42)
        elif si==0 and bar%2==0:
            self.emit('ghost',73,bar,.5,1.40,36)
        if si==6 and bar%8==7:
            self.emit('ghost',85,bar,1.875,.13,53)

    def drums(self,bar,si,density):
        # Drum machine rock-pop engine, staggered breakbeat-derived ornamentation.
        kick_positions=[0,2] if si in (1,2) else [0,1.5,2,3.5]
        if si==6:kick_positions=[0,1.5,2,3,3.75]
        snare_positions=[1,3]
        hats=[.5,1.5,2.5,3.5] if si==1 else [x*.5 for x in range(8)]
        if si==6: hats += [3.75]
        for p in kick_positions:self.emit('drums',GM_DRUMS['kick'],bar,p,.08,93 if p in (0,2) else 77)
        for p in snare_positions:self.emit('drums',GM_DRUMS['snare'],bar,p,.08,84)
        for p in hats:self.emit('drums',GM_DRUMS['closed_hat'],bar,p,.05,53 if (p*2)%2==0 else 42)
        if si>=2 and bar%4 in (1,3):
            self.emit('drums',GM_DRUMS['rim'],bar,2.75,.05,34)
        mutation=self.style('rhythm','drum_mutation') + self.weirdness[1]
        if mutation>=13 and bar%8==5:
            for p in (1.75,3.75):self.emit('drums',GM_DRUMS['rim'],bar,p,.045,39)
        if mutation>=15 and bar%4==3:
            self.emit('drums',GM_DRUMS['kick'],bar,3.75,.08,65)
        if si==6 and (self.variant=='strange' or self.weirdness[1]>=8) and bar%4==3:
            for p in (3.25,3.5,3.75):self.emit('drums',GM_DRUMS['low_tom'],bar,p,.07,53)
        if bar in (s.end-1 for s in self.sections if s.name!='RESIDUE / last bus'):
            self.emit('drums',GM_DRUMS['open_hat'],bar,3.5,.28,67)

    def write(self, filename: Path, parent: str|None=None):
        filename.parent.mkdir(parents=True,exist_ok=True)
        midi=MidiFile(type=1,ticks_per_beat=PPQ)
        conductor=MidiTrack(); midi.tracks.append(conductor)
        conductor.append(MetaMessage('track_name',name='Conductor',time=0))
        conductor.append(MetaMessage('set_tempo',tempo=bpm2tempo(self.bpm),time=0))
        conductor.append(MetaMessage('time_signature',numerator=4,denominator=4,time=0))
        conductor.append(MetaMessage('key_signature',key='A',time=0))
        last=0
        for s in self.sections:
            t=self.beat(s.start)
            conductor.append(MetaMessage('marker',text=s.name,time=t-last));last=t
        conductor.append(MetaMessage('end_of_track',time=self.beat(self.total_bars)-last))
        names={'chords':'01 Warm Voicings','bass':'02 Nervous Melodic Bass','guitar_a':'03 Clipped Guitar A',
               'guitar_b':'04 Reply Guitar B','lead':'05 Wistful Hook','ghost':'06 Ghost Synth',
               'drums':'07 Dry Machine Drums', 'sub_bass':'08 Low Sequenced Synth Bass'}
        for role in ['chords','bass','guitar_a','guitar_b','lead','ghost','drums','sub_bass']:
            tr=MidiTrack();midi.tracks.append(tr)
            tr.append(MetaMessage('track_name',name=names[role],time=0))
            events=[]
            for t,p,d,v in self.events[role]:
                events.append((t,1,Message('note_on',channel=self.track_channels[role],note=p,velocity=v,time=0)))
                events.append((t+d,0,Message('note_off',channel=self.track_channels[role],note=p,velocity=0,time=0)))
            events.sort(key=lambda e:(e[0],e[1]))
            last=0
            for t,_,msg in events:
                msg.time=t-last; tr.append(msg);last=t
            tr.append(MetaMessage('end_of_track',time=0))
        midi.save(filename)
        manifest = {
            'schema':'MIDI_LAB_2.0', 'file':filename.name, 'profile':self.profile_id,
            'bpm':self.bpm,'seed':self.seed,'minutes_requested':self.minutes,
            'minutes_actual':round(self.total_bars*4/self.bpm,3),
            'total_bars':self.total_bars,'variant':self.variant,
            'parent':parent, 'motifs':self.motif_ledger,
            'style_assignments':self.assignments,
            'weirdness':dict(zip(('harmonic','rhythmic','form','register','texture'),self.weirdness)),
            'harmonic_plan':{'base':[c['symbol'] for c in A_MAJOR],'contrast':[c['symbol'] for c in BRIDGE]},
            'sections':[dict(name=s.name,start_bar=s.start+1,end_bar=s.end,energy=s.energy,roles=list(s.roles)) for s in self.sections],
            'note':'Sound selection remains with the producer in their DAW; no Program Changes or Bank Selects.',
            'sub_bass_active':bool(self.events['sub_bass'])
        }
        man_file=filename.with_suffix('.manifest.json')
        man_file.write_text(json.dumps(manifest,indent=2),encoding='utf8')
        return filename,man_file


def extract_midi(path:Path):
    file=MidiFile(path)
    tracks=[]
    markers=[]
    tempo_us=500000
    invalid={'program_changes':0,'bank_selects':0,'unmatched_note_offs':0,'hanging_notes':0,'zero_length_notes':0}
    all_notes=[]
    for ti,tr in enumerate(file.tracks):
        absolute=0; name=f'Track {ti+1}'
        active=collections.defaultdict(list)
        notes=[]
        for msg in tr:
            absolute+=msg.time
            if msg.is_meta:
                if msg.type=='track_name': name=msg.name
                if msg.type=='marker': markers.append((absolute,msg.text))
                if msg.type=='set_tempo' and tempo_us==500000:tempo_us=msg.tempo
                continue
            if msg.type=='program_change':invalid['program_changes']+=1
            if msg.type=='control_change' and msg.control in (0,32):invalid['bank_selects']+=1
            if msg.type=='note_on' and msg.velocity>0:
                active[(msg.channel,msg.note)].append((absolute,msg.velocity))
            elif msg.type=='note_off' or (msg.type=='note_on' and msg.velocity==0):
                key=(msg.channel,msg.note)
                if not active[key]:invalid['unmatched_note_offs']+=1
                else:
                    start,velocity=active[key].pop(0)
                    if absolute<=start:invalid['zero_length_notes']+=1
                    notes.append((start,absolute,msg.note,velocity,msg.channel))
        invalid['hanging_notes']+=sum(len(x) for x in active.values())
        if notes:
            notes.sort(key=lambda n:(n[0],n[2]))
            tracks.append((name,notes));all_notes+=notes
    if not all_notes:return {'file':path.name,'type':file.type,'ppq':file.ticks_per_beat,'validation':invalid,'tracks':[], 'warnings':['No note events detected']}
    def stats(notes):
        starts=[n[0] for n in notes]
        pitches=[n[2] for n in notes]
        unique_onsets=len(set(starts))
        eighth=file.ticks_per_beat/2
        accents=sum(min(t%eighth,eighth-(t%eighth))>12 for t in starts)
        offbeats=sum(abs((t%file.ticks_per_beat)-eighth)<=12 for t in starts)
        intervals=[b-a for a,b in zip(pitches,pitches[1:])]
        counts=collections.Counter(PITCH_CLASSES[p%12] for p in pitches)
        return dict(note_count=len(notes),pitch_min=min(pitches),pitch_max=max(pitches),
                    median_pitch=round(statistics.median(pitches),1),unique_onsets=unique_onsets,
                    sixteenth_or_irregular_ratio=round(accents/len(notes),3),
                    offbeat_eighth_ratio=round(offbeats/len(notes),3),
                    pitch_classes=dict(counts.most_common(6)),
                    most_common_intervals=collections.Counter(intervals).most_common(5),
                    average_velocity=round(statistics.mean(n[3] for n in notes),1))
    duration_ticks=max(n[1] for n in all_notes)
    report={'file':path.name,'type':file.type,'ppq':file.ticks_per_beat,
        'approx_duration_quarter_notes':round(duration_ticks/file.ticks_per_beat,2),
        'validation':invalid,'total_notes':len(all_notes),
        'tracks':[dict(name=name,**stats(notes)) for name,notes in tracks]}
    markers.sort(key=lambda x:x[0])
    section_activity=[]
    for i,(start,label) in enumerate(markers):
        end=markers[i+1][0] if i+1<len(markers) else duration_ticks
        if end<=start:continue
        section_notes=[n for n in all_notes if start<=n[0]<end]
        section_activity.append({'section':label,
            'start_bar':round(start/file.ticks_per_beat/4+1,1),
            'notes_per_bar':round(len(section_notes)/max(1,(end-start)/file.ticks_per_beat/4),2),
            'active_roles':sum(bool([n for n in notes if start<=n[0]<end]) for _,notes in tracks)})
    report['arrangement_activity']=section_activity
    # Descriptive groove relationship; a shared downbeat is often a good thing.
    bass_tracks=[notes for name,notes in tracks if 'bass' in name.lower()]
    drum_tracks=[notes for name,notes in tracks if any(x in name.lower() for x in ('drum','perc','grid'))]
    if bass_tracks and drum_tracks:
        bass_onsets={round(n[0]/file.ticks_per_beat*4) for n in bass_tracks[0]}
        kick_onsets={round(n[0]/file.ticks_per_beat*4) for n in drum_tracks[0] if n[2]==36}
        common=len(bass_onsets & kick_onsets)
        report['bass_kick_alignment_ratio']=round(common/max(1,len(bass_onsets)),3)
    report['musical_heuristics'] = {
        'note_density_per_bar':round(len(all_notes)/max(1,duration_ticks/file.ticks_per_beat/4),2),
        'instrument_parts':len(tracks),
        'estimated_tempo_bpm':round(60000000/tempo_us,2),
        'caveat':'These measurements are structural proxies, not proof that the music sounds good.'
    }
    return report


def audit(path:Path):
    data=extract_midi(path)
    problems=data['validation']
    flags=[]
    if data['type']!=1:flags.append('Export should be MIDI Type 1')
    if data['ppq']!=480:flags.append('PPQ differs from house default 480')
    for k,v in problems.items():
        if v:flags.append(f'{k}: {v}')
    if len(data.get('arrangement_activity',[]))>=3:
        rates=[x['notes_per_bar'] for x in data['arrangement_activity']]
        if max(rates)-min(rates)<1.5:flags.append('Arrangement has very little change in note density across markers')
    for tr in data.get('tracks',[]):
        if tr['note_count']<4:flags.append(f'{tr["name"]}: fewer than four notes')
        if tr['pitch_max']-tr['pitch_min']>48:flags.append(f'{tr["name"]}: register spans over 4 octaves')
    data['audit']={'passed_technical':not any([data['type']!=1, data['ppq']!=480, *problems.values()]),
                   'flags':flags,
                   'unscored_checks':['Is the hook emotionally memorable?', 'Is the chorus different beyond added loudness?',
                                      'Does the bass have identity?', 'Are the parts competing for the same space?',
                                      'Are rhythmic surprises derived from earlier material?',
                                      'Do the parts suit the DAW instruments?', 'Is there sufficient silence?']}
    return data


def run():
    parser=argparse.ArgumentParser(description='MIDI Lab v2 | cook, variant, analyze, audit, benchmark, feedback')
    sub=parser.add_subparsers(dest='cmd',required=True)
    cook=sub.add_parser('cook');cook.add_argument('--profile',default='drums_solo_brutalism')
    cook.add_argument('--bpm',type=int,default=123);cook.add_argument('--minutes',type=float,default=3.25)
    cook.add_argument('--seed',type=int,default=271828)
    for axis in ('harmony','rhythm','bass','melody','arrangement'):
        cook.add_argument('--'+axis,help=f'Profile providing the {axis} role; defaults to --profile')
    cook.add_argument('--weirdness',default='3,4,2,2,4',help='Five 0–10 values H,R,Form,Register,Texture')
    cook.add_argument('--variant',choices=['default','restrained','melodic','strange'],default='default')
    cook.add_argument('--performance',choices=['none','tight','natural','loose','neworder'],default='none',help='Instrument-aware MIDI performance treatment')
    cook.add_argument('--output',type=Path,default=ROOT/'examples'/'after_the_sunline.mid')
    var=sub.add_parser('variant');var.add_argument('--manifest',type=Path,required=True)
    var.add_argument('--mode',choices=['restrained','melodic','strange'],required=True)
    var.add_argument('--output',type=Path,required=True)
    for name in ('analyze','audit'):
        p=sub.add_parser(name);p.add_argument('--input',type=Path,required=True)
        p.add_argument('--output',type=Path,default=None)
    bench=sub.add_parser('benchmark');bench.add_argument('--folder',type=Path,default=ROOT/'benchmarks')
    bench.add_argument('--output',type=Path,default=ROOT/'reports'/'benchmark_summary.json')
    fb=sub.add_parser('feedback');fb.add_argument('--track',required=True);fb.add_argument('--part',default='whole track')
    fb.add_argument('--rating',type=int,choices=range(1,6),required=True,metavar='1-5')
    fb.add_argument('--note',required=True);fb.add_argument('--tags',default='')
    a=parser.parse_args()
    if a.cmd=='cook':
        if not (40<=a.bpm<=220 and 0.5<=a.minutes<=12):parser.error('BPM 40–220; minutes 0.5–12')
        assignments={axis:getattr(a,axis) for axis in ('harmony','rhythm','bass','melody','arrangement') if getattr(a,axis)}
        try: weirdness=tuple(int(x) for x in a.weirdness.split(','))
        except ValueError:parser.error('--weirdness needs five comma-separated integers')
        c=Composer(a.profile,a.bpm,a.minutes,a.seed,a.variant,assignments,weirdness).compose()
        midi,manifest=c.write(a.output)
        if a.performance != 'none':
            from performance import apply_performance
            performed_path=midi.with_name(midi.stem+'_performed'+midi.suffix)
            perf_report=apply_performance(midi,performed_path,a.performance,a.seed)
            performed_path.replace(midi)
            perf_report['output']=str(midi)
            midi.with_suffix('.performance.json').write_text(json.dumps(perf_report,indent=2),encoding='utf8')
            m=json.loads(manifest.read_text(encoding='utf8'))
            m['performance']=a.performance
            manifest.write_text(json.dumps(m,indent=2),encoding='utf8')
        result=audit(midi)
        report=midi.with_suffix('.audit.json');report.write_text(json.dumps(result,indent=2),encoding='utf8')
        print(json.dumps({'midi':str(midi),'manifest':str(manifest),'audit':str(report),
                          'technical_pass':result['audit']['passed_technical'],'sections':len(c.sections),
                          'bars':c.total_bars,'minutes':round(c.total_bars*4/c.bpm,2)},indent=2))
        if not result['audit']['passed_technical']:raise SystemExit('Technical audit FAILED')
    elif a.cmd=='variant':
        parent=json.loads(a.manifest.read_text())
        assignments=parent.get('style_assignments')
        weirdness=tuple(parent.get('weirdness',{'harmonic':3,'rhythmic':4,'form':2,'register':2,'texture':4}).values())
        c=Composer(parent['profile'],parent['bpm'],parent['minutes_requested'],parent['seed'],a.mode,
                   assignments,weirdness).compose()
        midi,manifest=c.write(a.output,str(a.manifest))
        result=audit(midi)
        midi.with_suffix('.audit.json').write_text(json.dumps(result,indent=2))
        print(json.dumps({'midi':str(midi),'manifest':str(manifest),'technical_pass':result['audit']['passed_technical']},indent=2))
    elif a.cmd in ('analyze','audit'):
        data=extract_midi(a.input) if a.cmd=='analyze' else audit(a.input)
        if a.output:a.output.write_text(json.dumps(data,indent=2),encoding='utf8')
        print(json.dumps(data,indent=2))
    elif a.cmd=='benchmark':
        rows=[]
        for path in sorted(a.folder.glob('*.mid')):
            stats=audit(path)
            rows.append({'file':path.name,'note_count':stats.get('total_notes',0),
                         'tracks':len(stats.get('tracks',[])),
                         'note_density_per_bar':stats.get('musical_heuristics',{}).get('note_density_per_bar'),
                         'technical_pass':stats['audit']['passed_technical'],
                         'flags':stats['audit']['flags']})
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps({'tracks':rows,'note':'Baseline comparisons, not objective quality rankings'},indent=2))
        print(a.output, '\n', json.dumps(rows,indent=2))
    elif a.cmd=='feedback':
        ledger_path=ROOT/'taste_ledger.json'
        ledger=json.loads(ledger_path.read_text())
        ledger['feedback'].append({'track':a.track,'part':a.part,'rating':a.rating,
                                  'note':a.note,'tags':[x.strip() for x in a.tags.split(',') if x.strip()]})
        ledger_path.write_text(json.dumps(ledger,indent=2),encoding='utf8')
        print('Feedback recorded in:',ledger_path)

if __name__=='__main__':run()
