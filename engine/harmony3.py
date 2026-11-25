"""MIDI Lab 3.0: key-independent diatonic/modal progressions and smooth voicing selection.
No third-party dependencies. Rule-based composition, not chord transcription.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product

NAMES = ('C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B')
KEYS = {k:i for i,k in enumerate(NAMES)}
KEYS.update({'Db':1, 'D#':3, 'Gb':6, 'G#':8, 'A#':10, 'B#':0, 'Cb':11, 'Fb':4})
MODES = {
    'major': (0,2,4,5,7,9,11),
    'minor': (0,2,3,5,7,8,10),
    'dorian': (0,2,3,5,7,9,10),
    'mixolydian': (0,2,4,5,7,9,10),
}
PROGRESSIONS = {
    'major': {
        'tender': (1,3,6,4,2,5,4,5),
        'driving': (6,4,1,5,6,4,2,5),
        'hazy': (1,4,6,5,3,6,4,5),
        'bright': (1,5,6,4,1,3,4,5),
    },
    'minor': {
        'tender': (1,6,3,7,4,6,2,5),
        'driving': (1,6,3,7,1,4,6,7),
        'hazy': (1,4,6,3,7,6,4,5),
        'bright': (6,3,7,1,6,4,3,7),
    }
}

@dataclass(frozen=True)
class Chord:
    degree: int
    root_pc: int
    pcs: tuple[int,...]
    symbol: str
    borrowed: bool=False
    def as_dict(self):
        return dict(degree=self.degree,root_pc=self.root_pc,pcs=list(self.pcs),symbol=self.symbol,borrowed=self.borrowed)


def normalize_key(value: str) -> int:
    value=value.strip().replace('♯','#').replace('♭','b')
    if len(value)>1:value=value[0].upper()+value[1:]
    else:value=value.upper()
    if value not in KEYS:raise ValueError(f'Invalid tonic {value}. Try C, F#, Bb, etc.')
    return KEYS[value]


def degree_chord(key_pc:int,mode:str,degree:int,extension:str='seventh',borrowed:bool=False)->Chord:
    if mode not in MODES:raise ValueError('Unsupported mode: '+mode)
    if not 1<=degree<=7:raise ValueError('Degree must be 1..7')
    scale=MODES[mode]
    notes=[(key_pc+scale[(degree-1+2*i)%7])%12 for i in range(4)]
    root=notes[0]
    if borrowed:
        # Minor iv in major / borrowed bVI-ish major in minor; needs intentional contextual use
        if mode in ('major','mixolydian'):
            root=(key_pc+5)%12; notes=[root,(root+3)%12,(root+7)%12,(root+9)%12]
        else:
            root=(key_pc+8)%12; notes=[root,(root+4)%12,(root+7)%12,(root+11)%12]
    rel={(n-root)%12 for n in notes}
    triad='m' if 3 in rel else 'dim' if 6 in rel else ''
    if borrowed: triad='m6' if mode in ('major','mixolydian') else 'maj7'
    else:
        ext=('maj7' if 11 in rel else '7') if extension=='seventh' else ''
        if triad=='m' and ext=='maj7':ext='(maj7)'
        symbol=NAMES[root]+triad+ext
    if borrowed:symbol=NAMES[root]+triad+' (borrowed)'
    pcs=tuple(dict.fromkeys(notes))
    return Chord(degree,root,pcs,symbol,borrowed)


def select_progression(key_pc:int,mode:str,mood:str='tender',length:int=8)->list[Chord]:
    base_mode='major' if mode in ('major','mixolydian') else 'minor'
    degrees=PROGRESSIONS[base_mode].get(mood,PROGRESSIONS[base_mode]['tender'])
    return [degree_chord(key_pc,mode,degrees[i%len(degrees)]) for i in range(length)]


def section_chords(key_pc:int,mode:str,mood:str='tender',section:int=0)->list[Chord]:
    base=select_progression(key_pc,mode,mood,8)
    if section==4:  # quieter bridge: related but different order, one purposeful borrowing
        bridge=[base[5],base[3],base[2],base[4],base[1],base[3],base[0],base[4]]
        bridge[3]=degree_chord(key_pc,mode,4,borrowed=True)
        return bridge
    if section==6:  # final refrain: harmonic recoloring rather than just more tracks
        alt=list(base)
        alt[6]=degree_chord(key_pc,mode,4,borrowed=True)
        return alt
    if section==5:
        return [base[i] for i in (2,3,1,4,2,3,4,0)]
    return base


def voice_lead(chord:Chord, prev:tuple[int,...]|None=None, lo:int=49,hi:int=77, voices:int=4)->tuple[int,...]:
    """Enumerate playable keyboard note-set placements and minimize voice motion.
    Unlike a per-voice octave snap, this selects one actual voicing collectively.
    """
    tones=chord.pcs[:voices]
    candidates=[]
    for pc in tones:
        candidates.append([n for n in range(lo,hi+1) if n%12==pc])
    ranked=[]
    for combo in product(*candidates):
        pitches=tuple(sorted(combo))
        if len(set(pitches))!=len(pitches):continue
        span=pitches[-1]-pitches[0]
        if span>23 or span<9:continue
        # Favor good midrange, coherent shape, and small upper register contour.
        spacing=sum(max(0,3-(b-a))*1.3 for a,b in zip(pitches,pitches[1:]))
        placement=abs(sum(pitches)/len(pitches)-62)*.20
        if prev:
            prev_sorted=sorted(prev)
            voice_motion=sum(abs(a-b) for a,b in zip(pitches,prev_sorted))
            common=sum(1 for n in pitches if n in prev_sorted)
            voice_lead_cost=voice_motion*1.65 - common*2.5
            top_jump=max(0,abs(pitches[-1]-prev_sorted[-1])-5)*2
        else:
            voice_lead_cost=0;top_jump=0
        ranked.append((voice_lead_cost+top_jump+spacing+placement+abs(span-17)*.25,pitches))
    if not ranked:
        raise ValueError(f'Cannot voice {chord.symbol} in requested register')
    return min(ranked,key=lambda x:x[0])[1]


def bass_root(chord:Chord,octave:int=2)->int:
    """C2 = 36; pitch class numbers are not octave numbers."""
    return 36+chord.root_pc+12*(octave-2)
