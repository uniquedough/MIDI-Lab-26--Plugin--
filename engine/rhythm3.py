"""MIDI Lab 3.0: six distinct groove families using authored rhythmic cells.
Events: (beat position, General MIDI drum pitch, velocity, duration in quarter beats).
Rhythmic mutation is derived from a stable groove; it is never unrestricted random noise.
"""
from __future__ import annotations

KICK=36; SNARE=38; RIM=37; HAT=42; OHAT=46; SHAKE=70; TOM=45; CLAP=39
ENGINES=('ballad','postpunk','motorik','ukg','jungle','eurodance','idm','minimal')

def infer_engine(profile_id:str):
    p=profile_id.lower()
    if any(x in p for x in ('ukg','2step','garage','pink_bedroom','pink_fancy')):return 'ukg'
    if 'jungle' in p or 'liquid' in p:return 'jungle'
    if 'eurodance' in p:return 'eurodance'
    if 'idm' in p:return 'idm'
    if any(x in p for x in ('tender_nocturne','afterhours','drums_solo_jonny')):return 'ballad'
    if any(x in p for x in ('technique','lowlife','lcd_motor','neon_motor','yl_motorik')):return 'motorik'
    if any(x in p for x in ('movement','brotherhood','pcl','drums_solo_abysmal')):return 'postpunk'
    return 'minimal'

def render_bar(engine:str,bar:int,energy:float,mutation:int=4,fill:bool=False,swing:float=.0):
    if engine not in ENGINES:raise ValueError(f'Unknown engine {engine}; choose {ENGINES}')
    ev=[]
    def add(p,n,v,d=.07):
        if 0<=p<4:ev.append((round(p,4),n,max(1,min(127,int(v))),d))
    if engine=='ballad':
        for p in (0,2.5):add(p,KICK,72 if p==0 else 57)
        for p in (1,3):add(p,RIM,54)
        for p in (.5,1.5,2.5,3.5):add(p,HAT,38 if p%1 else 46)
        if mutation>=6 and bar%8==6:add(3.75,RIM,24)
    elif engine=='postpunk':
        for p in (0,2,2.75 if bar%4==3 else 3.5):add(p,KICK,88 if p in (0,2) else 64)
        for p in (1,3):add(p,SNARE,82 if p==1 else 90)
        for i in range(8):add(i*.5,HAT,48 if i%2 else 60)
        if mutation>=5 and bar%4==3:add(3.75,RIM,32)
    elif engine=='motorik':
        for p in (0,1,2,3):add(p,KICK,94 if p in (0,2) else 83)
        for p in (1,3):add(p,SNARE,82)
        for i in range(8):add(i*.5,HAT,53 if i%2==0 else 44)
        if bar%4==3:add(3.5,OHAT,57)
        if mutation>=7 and bar%8==6:add(3.75,RIM,29)
    elif engine=='ukg':
        # Syncopated kick, skippy offbeats, late hats. Swing applied to the offbeat 8ths.
        kicks= [0,1.75,2.5] if bar%2==0 else [0,.75,2.75,3.5]
        for p in kicks:add(p,KICK,89 if p==0 else 72)
        for p in (1,3):add(p,SNARE,81 if p==1 else 87)
        for i,p in enumerate((.5,1.5,2.0,2.5,3.5)):
            add(p+(swing if abs(p-round(p))>.1 else 0),HAT,49 if i%2 else 59)
        for p in (1.75,3.75):
            if (bar+p)%2>.5 or mutation>=6:add(p,RIM,30)
        if bar%4==3:add(3.375,OHAT,43)
    elif engine=='jungle':
        # Fast broken funk-derived cells with stable backbeat and derived ghosts.
        kick_pat= (0,1.625,2.5) if bar%2==0 else (0,.75,2.25,3.625)
        for p in kick_pat:add(p,KICK,86 if p==0 else 68)
        for p in (1,3):add(p,SNARE,88)
        for p in (.75,2.75,3.375):add(p,RIM,37 if p!=2.75 else 44)
        for i in range(16):
            if i%4!=3 or mutation>=5:add(i*.25,HAT,42 if i%2 else 59,.035)
        if bar%4==3:add(3.75,SNARE,43)
    elif engine=='eurodance':
        for p in (0,1,2,3):add(p,KICK,105 if p in (0,2) else 91)
        for p in (1,3):add(p,CLAP,89)
        for p in (.5,1.5,2.5,3.5):add(p,OHAT,63)
        for i in range(8):add(i*.5,HAT,37 if i%2 else 44)
        if mutation>=6 and bar%4==3:add(3.75,RIM,40)
    elif engine=='idm':
        # An anchor plus a 3-3-2 derived kick cell, not independent randomized notes.
        kick_pat=(0,.75,1.5,2.5) if bar%4<2 else (0,1.25,2.25,3.5)
        for p in kick_pat:add(p,KICK,88 if p==0 else 67)
        for p in (1,3):add(p,SNARE,78)
        hats=[0,.375,.75,1.5,2.25,2.625,3.5]
        if bar%4==3:hats=[p for p in hats if p not in (.75,2.625)]
        for i,p in enumerate(hats):add(p,HAT,47+(i%3)*7,.035)
        if mutation>=6 and bar%4==3:add(3.75,TOM,53)
    else: # minimal
        for p in (0,2):add(p,KICK,75)
        for p in (1,3):add(p,RIM,56)
        for p in (.5,1.5,2.5,3.5):add(p,HAT,43)
    if fill:
        # Fill derived from the main snare sound, staying in the final half beat.
        if engine in ('jungle','idm'):add(3.75,RIM,48)
        elif engine not in ('ballad','minimal'):add(3.75,SNARE,47)
    # Lower energy means subtracting auxiliary events, not simply scaling all velocities.
    if energy<.3:
        ev=[(p,n,max(20,int(v*.66)),d) for p,n,v,d in ev if (n in (KICK,SNARE,RIM)) or (n in (HAT,OHAT) and p in (.5,2.5))]
    elif energy<.5:
        ev=[(p,n,int(v*.83),d) for p,n,v,d in ev if n not in (TOM,SHAKE) and not (n==HAT and p>=3)]
    return ev
