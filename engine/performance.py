#!/usr/bin/env python3
"""MIDI Lab v2.4 instrument-aware performance treatment.

Works on Type 1 or Type 0 MIDI. Preserves patch freedom: no Program Change,
no Bank Select CC 0/32. Preserves conductor/markers and note-on/off pairing.

Usage:
 python performance.py --input examples/foo.mid --output examples/foo_performed.mid \
   --feel neworder --seed 24
 python performance.py --input track.mid --output performed.mid \
   --mapping instruments.json --feel natural

Mapping JSON can identify track names by substring, e.g.
 {"Nervous Melodic Bass": "picked_bass", "Warm Voicings":"organ", "Dry Machine":"drum_machine"}
"""
from __future__ import annotations
import argparse, collections, json, random, math
from pathlib import Path
from mido import MidiFile, MidiTrack, Message, MetaMessage

# Soft defaults, not strict biological rules. Values are compatible with sample-based instruments.
INSTRUMENTS={
 'picked_bass': dict(lo=53,hi=111,timing=5,gate=.91,shape='pick'),
 'finger_bass': dict(lo=45,hi=102,timing=8,gate=.98,shape='finger'),
 'sub_synth':dict(lo=64,hi=94,timing=0,gate=.90,shape='fixed'),
 'clipped_guitar':dict(lo=53,hi=98,timing=7,gate=.78,shape='pick'),
 'ringing_guitar':dict(lo=49,hi=100,timing=10,gate=1.04,shape='guitar'),
 'piano':dict(lo=34,hi=110,timing=4,gate=.94,shape='key'),
 'organ':dict(lo=50,hi=84,timing=2,gate=.98,shape='organ'),
 'analog_synth':dict(lo=54,hi=94,timing=1,gate=.93,shape='fixed'),
 'pad':dict(lo=42,hi=80,timing=2,gate=1.03,shape='organ'),
 'lead_synth':dict(lo=46,hi=104,timing=3,gate=.92,shape='key'),
 'drum_machine':dict(lo=30,hi=116,timing=0,gate=1.,shape='drum_machine'),
 'live_drums':dict(lo=25,hi=116,timing=7,gate=1.,shape='drum_live'),
}

def infer(name,drum_channel=False):
 if drum_channel:return 'drum_machine'
 s=name.lower()
 if ('sub' in s or 'low sequenc' in s):return 'sub_synth'
 if 'bass' in s:return 'picked_bass'
 if ('guitar' in s or 'interlock' in s):return 'clipped_guitar' if any(x in s for x in ('clipped','pluck','interlock')) else 'ringing_guitar'
 if any(x in s for x in ('rhodes','piano','electric keys')):return 'piano'
 if any(x in s for x in ('organ','warm voicing','chord')):return 'organ'
 if any(x in s for x in ('drum','percussion','grid')):return 'drum_machine'
 if any(x in s for x in ('pad','haze')):return 'pad'
 if any(x in s for x in ('lead','hook','motif')):return 'lead_synth'
 return 'analog_synth'

def shape_velocity(original,beatpos,pitch,instrument,rng,feel):
 cfg=INSTRUMENTS[instrument]
 # Preserve original dynamics as a very significant input.
 x=max(0.,min(1.,(original-26)/96))
 phase=beatpos%1
 down=abs(phase)<.12
 off=abs(phase-.5)<.12
 s=cfg['shape']
 if s=='pick':accent=11 if down else 3 if off else -7
 elif s=='finger':accent=6 if down else 0 if off else -5
 elif s=='guitar':accent=7 if down else 1 if off else -2
 elif s=='key':accent=5 if down else -2
 elif s=='organ':accent=2 if down else 0
 elif s=='fixed':accent=3 if down else 0
 else:accent=0
 if s in ('drum_machine','drum_live'):
  if pitch==36: base=99 if down else 87; spread=3 if s=='drum_machine' else 7
  elif pitch==38: base=95 if original>=65 else 39;spread=3 if s=='drum_machine' else 10
  elif pitch==37:base=39 if original<=55 else 66;spread=4 if s=='drum_machine' else 9
  elif pitch in (42,44,46):
   base=68 if down else 51 if off else 46
   if original<45:base=39
   spread=4 if s=='drum_machine' else 12
  else:base=69;spread=5 if s=='drum_machine' else 12
  if feel=='tight':spread=max(1,spread//2)
  elif feel=='loose':spread*=2
  return max(1,min(127,round(.7*base+.3*original+rng.gauss(0,spread))))
 lo,hi=cfg['lo'],cfg['hi']
 # Preserve broad source intention, layer onto accent curve and narrow/expand
 source=.58*x+.42*.52
 v=lo+(hi-lo)*source+accent
 if instrument=='picked_bass' and original<=58:v-=7 # pickup/ghost note
 if instrument=='clipped_guitar' and original<=58:v-=5
 rand= {'tight':1.5,'natural':4.0,'loose':8.0,'neworder':3.2}[feel]
 if s=='fixed' or (feel=='neworder' and instrument in ('analog_synth','sub_synth')):rand=min(rand,1.25)
 v+=rng.gauss(0,rand)
 return max(1,min(127,round(v)))

def apply_performance(src:Path,dst:Path,feel='natural',seed=1086,mapping=None):
 if feel not in ('tight','natural','loose','neworder'):raise ValueError('Unknown feel')
 rng=random.Random(seed)
 mid=MidiFile(src)
 out=MidiFile(type=mid.type,ticks_per_beat=mid.ticks_per_beat)
 timing_mult={'tight':.35,'natural':1.0,'loose':1.7,'neworder':1.0}[feel]
 stat={'input':str(src),'output':str(dst),'feel':feel,'seed':seed,
       'notes':0,'program_changes_removed':0,'bank_selects_removed':0,
       'tracks':{},'min_duration_ticks':None}
 mapdata=mapping or {}
 for ti,tr in enumerate(mid.tracks):
  name=next((msg.name for msg in tr if msg.is_meta and msg.type=='track_name'),f'Track {ti+1}')
  ev=[]; open_notes=collections.defaultdict(list); tick=0; channel_counts=collections.Counter()
  for msg in tr:
   tick+=msg.time
   if not msg.is_meta and msg.type=='program_change':
    stat['program_changes_removed']+=1;continue
   if not msg.is_meta and msg.type=='control_change' and msg.control in (0,32):
    stat['bank_selects_removed']+=1;continue
   if not msg.is_meta and msg.type=='note_on' and msg.velocity>0:
    open_notes[(msg.channel,msg.note)].append((tick,msg.velocity))
    channel_counts[msg.channel]+=1
   elif not msg.is_meta and (msg.type=='note_off' or (msg.type=='note_on' and msg.velocity==0)):
    key=(msg.channel,msg.note)
    if open_notes[key]:
     start,velocity=open_notes[key].pop(0)
     ev.append((start,tick,key[0],key[1],velocity))
    else:
     raise ValueError(f'Unmatched note off {key} in {name}')
   elif not (msg.is_meta and msg.type=='end_of_track'):
    ev.append((tick,'other',msg.copy(time=0)))
  if any(open_notes.values()):raise ValueError(f'Hanging notes in {name}')
  remaining=[]; performed=[]
  for event in ev:
   if len(event)==3 and event[1]=='other':
    remaining.append((event[0],2,event[2]));continue
   start,end,ch,pitch,velocity=event
   instr=next((v for k,v in mapdata.items() if k.lower() in name.lower()),None)
   instr=instr or infer(name,drum_channel=(ch==9))
   if instr not in INSTRUMENTS:raise ValueError(f'Unknown instrument mapping: {instr}')
   cfg=INSTRUMENTS[instr]
   # No potentially destructive random drift for machine events.
   timing_ticks=round(cfg['timing']*timing_mult)
   if feel=='neworder' and instr in ('sub_synth','analog_synth','drum_machine'):timing_ticks=0
   delta=rng.randint(-timing_ticks,timing_ticks) if timing_ticks else 0
   st=max(0,start+delta)
   original_dur=max(1,end-start)
   gate=1. if ch==9 else cfg['gate']
   if feel=='loose' and instr in ('ringing_guitar','finger_bass'):gate*=1.03
   dur=max(2,round(original_dur*gate))
   v=shape_velocity(velocity,st/mid.ticks_per_beat,pitch,instr,rng,feel)
   performed.append([st,st+dur,ch,pitch,v,instr])
   stat['notes']+=1
  # Don't allow an identical pitch/channel retrigger to leave accidental overlapping voices.
  slots=collections.defaultdict(list)
  for q in performed:slots[(q[2],q[3])].append(q)
  for slot in slots.values():
   slot.sort(key=lambda x:x[0])
   for a,b in zip(slot,slot[1:]):
    if a[1]>=b[0]:a[1]=max(a[0]+1,b[0]-1)
  for st,en,ch,pitch,vel,ins in performed:
   remaining.append((st,1,Message('note_on',channel=ch,note=pitch,velocity=vel,time=0)))
   remaining.append((en,0,Message('note_off',channel=ch,note=pitch,velocity=0,time=0)))
   dur=en-st
   stat['min_duration_ticks']=dur if stat['min_duration_ticks'] is None else min(stat['min_duration_ticks'],dur)
  remaining.sort(key=lambda x:(x[0],x[1]))
  target=MidiTrack(); last=0
  for at,_,msg in remaining:
   if at<last:raise AssertionError('Negative MIDI delta')
   target.append(msg.copy(time=at-last));last=at
  target.append(MetaMessage('end_of_track',time=0))
  out.tracks.append(target)
  if performed:
   types=collections.Counter(x[-1] for x in performed)
   stat['tracks'][name]={'notes':len(performed),'instruments':dict(types),
       'velocity_min':min(x[4] for x in performed),'velocity_max':max(x[4] for x in performed),
       'velocity_average':round(sum(x[4] for x in performed)/len(performed),1)}
 dst.parent.mkdir(parents=True,exist_ok=True)
 out.save(dst)
 # Structural check, plus check forbidden events in output
 check=MidiFile(dst)
 on=off=pc=bank=0
 for tr in check.tracks:
  for msg in tr:
   if msg.is_meta:continue
   if msg.type=='program_change':pc+=1
   if msg.type=='control_change' and msg.control in (0,32):bank+=1
   if msg.type=='note_on' and msg.velocity>0:on+=1
   if msg.type=='note_off' or (msg.type=='note_on' and msg.velocity==0):off+=1
 stat['check']={'note_ons':on,'note_offs':off,'program_changes':pc,'bank_selects':bank,
                'passed':on==off==stat['notes'] and pc==bank==0}
 if not stat['check']['passed']:raise AssertionError('Output validation failed')
 return stat

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--input',required=True,type=Path)
 p.add_argument('--output',required=True,type=Path)
 p.add_argument('--feel',default='natural',choices=['tight','natural','loose','neworder'])
 p.add_argument('--seed',type=int,default=1086)
 p.add_argument('--mapping',type=Path,default=None,help='Optional JSON substring-to-instrument mapping')
 args=p.parse_args()
 mapping=json.loads(args.mapping.read_text()) if args.mapping else None
 report=apply_performance(args.input,args.output,args.feel,args.seed,mapping)
 path=args.output.with_suffix('.performance.json')
 path.write_text(json.dumps(report,indent=2))
 print(json.dumps({'midi':str(args.output),'report':str(path),'validation':report['check']},indent=2))

if __name__=='__main__':main()
