"""MIDI Lab v3.0 quantitative analyzer. Does NOT assess emotional quality by numbers alone."""
from __future__ import annotations
import collections,json,statistics,math
from pathlib import Path
from mido import MidiFile

def analyze(path:Path,manifest=None):
    path=Path(path);m=MidiFile(path)
    validation=dict(program_changes=0,bank_selects=0,unmatched_note_offs=0,hanging_notes=0,
                    zero_duration_notes=0,same_pitch_overlaps=0,negative_delta_times=0)
    notes_by_track={}; markers=[]; tempo_events=[]; total_tick=0
    for i,tr in enumerate(m.tracks):
        time=0;name=f'Track {i+1}';opened=collections.defaultdict(list);notes=[]
        for msg in tr:
            if msg.time<0:validation['negative_delta_times']+=1
            time+=msg.time
            if msg.is_meta:
                if msg.type=='track_name':name=msg.name
                if msg.type=='marker':markers.append((time,msg.text))
                if msg.type=='set_tempo':tempo_events.append((time,msg.tempo))
                continue
            if msg.type=='program_change':validation['program_changes']+=1
            if msg.type=='control_change' and msg.control in (0,32):validation['bank_selects']+=1
            if msg.type=='note_on' and msg.velocity>0:
                opened[(msg.channel,msg.note)].append((time,msg.velocity))
            if msg.type=='note_off' or (msg.type=='note_on' and msg.velocity==0):
                k=(msg.channel,msg.note)
                if not opened[k]:validation['unmatched_note_offs']+=1
                else:
                    start,vel=opened[k].pop(0)
                    if time<=start:validation['zero_duration_notes']+=1
                    notes.append((start,time,msg.note,vel,msg.channel))
        validation['hanging_notes']+=sum(len(x) for x in opened.values())
        if notes:
            notes_by_track[name]=sorted(notes)
            for ch,pitch in set((n[4],n[2]) for n in notes):
                seq=sorted((n for n in notes if n[4]==ch and n[2]==pitch),key=lambda x:x[0])
                validation['same_pitch_overlaps']+=sum(a[1]>b[0] for a,b in zip(seq,seq[1:]))
        total_tick=max(total_tick,time)
    if not tempo_events:tempo_events=[(0,500000)]
    tempo_events=sorted(set(tempo_events))
    # Piecewise tempo integration to report actual seconds even with tempo changes.
    t=0;elapsed=0.0;mpqn=500000
    for pos,next_tempo in tempo_events:
        if pos<t:continue
        elapsed+=(pos-t)/m.ticks_per_beat*mpqn/1e6;t=pos;mpqn=next_tempo
    elapsed+=(total_tick-t)/m.ticks_per_beat*mpqn/1e6
    all_notes=[n for ns in notes_by_track.values() for n in ns]
    drums=[n for name,ns in notes_by_track.items() if 'drum' in name.lower() or 'perc' in name.lower() for n in ns if n[4]==9]
    bass=[n for name,ns in notes_by_track.items() if 'bass' in name.lower() for n in ns]
    lead=[n for name,ns in notes_by_track.items() if any(w in name.lower() for w in ('hook','lead','motif')) for n in ns]
    ppq=m.ticks_per_beat
    def track_stats(name,notes):
        vel=[n[3] for n in notes]; pitches=[n[2] for n in notes]
        beats=[n[0]/ppq for n in notes]
        interval_seq=[b-a for a,b in zip(pitches,pitches[1:])]
        grid=collections.Counter(int(round((b%4)*4))%16 for b in beats)
        return dict(name=name,note_count=len(notes),register=[min(pitches),max(pitches)],
                    velocity={'min':min(vel),'mean':round(statistics.mean(vel),1),
                              'stdev':round(statistics.pstdev(vel),1),'max':max(vel)},
                    top_intervals=collections.Counter(interval_seq).most_common(5),
                    sixteenth_grid_counts={str(k):grid[k] for k in range(16) if grid[k]>0},
                    avg_note_length_beats=round(statistics.mean((n[1]-n[0])/ppq for n in notes),3))
    stats=[track_stats(name,ns) for name,ns in notes_by_track.items()]
    kick_starts={round(n[0]/ppq*4) for n in drums if n[2]==36}
    bass_starts={round(n[0]/ppq*4) for n in bass}
    kick_ratio=round(len(kick_starts&bass_starts)/len(bass_starts),3) if bass_starts else None
    markers=sorted(markers)
    activity=[]
    for i,(st,label) in enumerate(markers):
        en=markers[i+1][0] if i<len(markers)-1 else total_tick
        if en<=st:continue
        bars=(en-st)/(ppq*4)
        active={name:sum(st<=n[0]<en for n in ns) for name,ns in notes_by_track.items()}
        activity.append(dict(name=label,start_bar=round(st/ppq/4+1,1),end_bar=round(en/ppq/4,1),
                             notes_per_bar=round(sum(active.values())/bars,2),
                             active_roles=sum(x>0 for x in active.values()),part_counts=active))
    motifs=[]
    if lead:
        # Pitch contour n-grams from lead; descriptive, not copyright identification.
        seq=[n[2] for n in sorted(lead)]
        tokens=[tuple(seq[i+j+1]-seq[i+j] for j in range(3)) for i in range(len(seq)-3)]
        motifs=[{'contour':list(k),'occurrences':v} for k,v in collections.Counter(tokens).most_common(4)]
    elif bass:
        seq=[n[2] for n in sorted(bass)]
        tokens=[tuple(seq[i+j+1]-seq[i+j] for j in range(3)) for i in range(len(seq)-3)]
        motifs=[{'contour':list(k),'occurrences':v} for k,v in collections.Counter(tokens).most_common(4)]
    diagnostics=[]
    if activity:
        den=[x['notes_per_bar'] for x in activity]
        if max(den)-min(den)<2:diagnostics.append('Section density changes little; consider subtracting a role.')
        if activity[-2]['notes_per_bar']<=activity[1]['notes_per_bar']:
            diagnostics.append('Final return not denser than first verse (may be intentional).')
    if kick_ratio is not None and kick_ratio>=.88:
        diagnostics.append('Bass largely shadows kick timing; confirm this is intentional.')
    if lead and motifs and motifs[0]['occurrences']<2:
        diagnostics.append('Lead 4-note interval patterns repeat infrequently; check hook memory.')
    if not all_notes:diagnostics.append('No notes found.')
    manifest_data=None
    if manifest and Path(manifest).exists():
        manifest_data=json.loads(Path(manifest).read_text(encoding='utf8'))
    result={'file':path.name,'midi_type':m.type,'ppq':ppq,'duration_seconds':round(elapsed,2),
            'note_count':len(all_notes),'track_count':len(notes_by_track),'technical_pass':(
                m.type==1 and ppq==480 and not any(validation.values()) and bool(all_notes)),
            'validation':validation,'track_stats':stats,'activity_curve':activity,
            'bass_kick_onset_overlap':kick_ratio,'most_common_melodic_contours':motifs,
            'diagnostics':diagnostics,
            'quality_caveat':'These are structural features; ear-based critique is still required.'}
    if manifest_data:
        result['declared_key_mode']=f"{manifest_data.get('key')} {manifest_data.get('mode')}"
        result['declared_drum_engine']=manifest_data.get('drum_engine')
        result['borrowed_chord_occurrences']=sum(bool(x.get('borrowed')) for x in manifest_data.get('harmonic_sequence',[]))
        result['motif_operations']=dict(collections.Counter(x['operation'] for x in manifest_data.get('motif_reappearances',[])))
        result['fretboard_shape_fallbacks']=manifest_data.get('guitar_shape_fallbacks')
    return result

def compare(a,b):
    x,y=analyze(a),analyze(b)
    role_a={t['name']:t for t in x['track_stats']};role_b={t['name']:t for t in y['track_stats']}
    all_roles=sorted(set(role_a)|set(role_b))
    return {'a':x['file'],'b':y['file'],
            'note_count_delta_b_minus_a':y['note_count']-x['note_count'],
            'duration_delta_seconds':round(y['duration_seconds']-x['duration_seconds'],2),
            'role_note_count_delta':{k:role_b.get(k,{}).get('note_count',0)-role_a.get(k,{}).get('note_count',0) for k in all_roles},
            'bass_kick_overlap_a':x['bass_kick_onset_overlap'],
            'bass_kick_overlap_b':y['bass_kick_onset_overlap'],
            'note':'Quantitative only. A musical improvement needs an ear-based assessment.'}
