"""Fretboard-aware chord shapes and guitar articulations for standard-tuned six-string guitar.
Tuning: E2 A2 D3 G3 B3 E4 (MIDI 40 45 50 55 59 64).
"""
from __future__ import annotations
from itertools import product
TUNING=(40,45,50,55,59,64)

def chord_shape(pcs,prev=None,max_fret=12,max_span=4):
    """Find a 3/4-string chord grip with each selected string sounded at most once.
    Returns list of (string_index, fret, pitch), or None if no grip exists.
    """
    pcs=set(pcs)
    options=[]
    for open_pitch in TUNING:
        valid=[None]+[(f,open_pitch+f) for f in range(0,max_fret+1) if (open_pitch+f)%12 in pcs]
        options.append(valid)
    ranked=[]
    # Limit shaped attack to upper 4 strings for brighter indie guitar, playable chord grip.
    for a,b,c,d in product(*options[2:]):
        grip=[(i+2,t[0],t[1]) for i,t in enumerate((a,b,c,d)) if t is not None]
        if len(grip)<3:continue
        sounding={pitch%12 for _,_,pitch in grip}
        if len(sounding)<3:continue
        frets=[f for _,f,_ in grip if f>0]
        if frets and max(frets)-min(frets)>max_span:continue
        if any(f>max_fret for _,f,_ in grip):continue
        # Avoid very wide string jumps, over-high grips, extreme shifts.
        shift=abs((sum(f for _,f,_ in grip)/len(grip)) - (sum(x[1] for x in prev)/len(prev))) if prev else 0
        penalty= shift*1.6+sum(f for _,f,_ in grip)*.45+(.6 if len(grip)==3 else 0)
        penalty+=(5 if len(sounding)<min(4,len(pcs)) else 0)
        if max(p for _,_,p in grip)>78:penalty+=6
        ranked.append((penalty,grip))
    if not ranked:
        return None
    return min(ranked,key=lambda x:x[0])[1]

def arpeggio(grip,bar:int,density:str='medium'):
    """Return short plucks: (beat, MIDI pitch, duration, velocity).
    Each pitch is from the playable grip, including 1-string-per-note constraint.
    """
    notes=[x[2] for x in grip]
    if density=='sparse':steps=[(.5,0,.48,64),(2.5,-1,.52,60)]
    elif density=='full':steps=[(.25,0,.4,66),(1.25,1,.34,60),(2.0,2,.4,64),(3.0,-1,.38,57)]
    else:steps=[(.25,0,.4,67),(1.75,2,.43,60),(3.25,-1,.36,63)]
    return [(p,notes[i],d,v) for p,i,d,v in steps]
