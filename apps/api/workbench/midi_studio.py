"""Versioned, independent-track composition; every control maps to note behavior."""
import hashlib
import random
from .midi import ROOTS, SCALES
from .schemas import MidiCommand
from .harmony import harmonic_plan, chord_classes, choose_pitch, melodic_path

ENGINE = 'local_composition_v3'
MAX_NOTES = 50_000


def track_rng(seed: int, track: str, purpose: str) -> random.Random:
    digest=hashlib.sha256(f'{ENGINE}:{seed}:{track}:{purpose}'.encode()).digest()
    return random.Random(int.from_bytes(digest,'big'))


def compose_studio(command: MidiCommand, context_notes: list[dict] | None = None) -> list[dict]:
    p,s=command,command.settings
    if s is None:
        raise ValueError('MIDI Studio requires settings v2.')
    root,scale=ROOTS[p.key],SCALES[p.scale]
    harmony=harmonic_plan(p)
    total=p.bars*4
    notes=[]
    generated_tracks=set(s.enabled_tracks)
    if 'Countermelody' in generated_tracks and context_notes is None:
        generated_tracks.add('Melody')
    jitter={track:track_rng(p.seed,track,'performance') for track in generated_tracks}

    def degree(d):
        return root+scale[d%7]+12*(d//7)

    def fit(d,register,near=None):
        pc=degree(d)%12
        choices=[n for n in range(register.low,register.high+1) if n%12==pc]
        if not choices:
            raise ValueError('Pitch range cannot represent the requested harmony or melody; widen the range.')
        target=near if near is not None else (register.low+register.high)/2
        return min(choices,key=lambda n:(abs(n-target),n))

    def add(track,pitch,start,duration,accent=0):
        if track not in generated_tracks:
            return
        rng=jitter[track]
        # Swing eighth offbeats and alternate sixteenth hats in their own pair.
        subdivision=.25 if track=='Drums' and pitch==42 and s.hat_subdivision=='sixteenth' else .5
        pair=subdivision*2
        if abs((start%pair)-subdivision)<1e-7:
            start+=(s.swing/100-.5)*pair
        start+=rng.uniform(-s.timing_ms,s.timing_ms)*p.bpm/60000
        # Tick-quantized boundaries keep same-tick note-off/on ordering well defined.
        tick=max(0,min(total*480-1,round(start*480)))
        off=min(total*480,max(tick+1,round((start+duration)*480)))
        velocity=getattr(s,track.lower()+'_velocity')+accent+rng.randint(-s.velocity_variation,s.velocity_variation)
        notes.append({'track':track,'pitch':int(pitch),'start':tick/480,'duration':(off-tick)/480,
                      'velocity':max(1,min(127,velocity))})

    def voices(d,previous):
        count={'triad':3,'seventh':4,'ninth':5}[s.chord_type]
        base=[degree(d+2*i) for i in range(count)]
        candidates=[]
        for rotation in range(count):
            if not s.smooth_voice_leading and rotation != 0:
                continue
            chord=sorted(base[rotation:]+[n+12 for n in base[:rotation]])
            if s.voicing=='open':
                chord=sorted([n-12 if i==len(chord)-2 else n for i,n in enumerate(chord)])
            for shift in range(-24,121,12):
                candidate=[n+shift for n in chord]
                if min(candidate)>=s.chords_range.low and max(candidate)<=s.chords_range.high:
                    candidates.append(candidate)
        if not candidates:
            raise ValueError('No feasible chord voicing in this range; widen the chord range or simplify the chord type.')
        if previous and s.smooth_voice_leading:
            return min(candidates,key=lambda c:(sum(abs(a-b)+max(0,abs(a-b)-7)*2 for a,b in zip(c,previous)),abs(sum(c)/len(c)-62),c))
        return min(candidates,key=lambda c:(abs(sum(c)/len(c)-(s.chords_range.low+s.chords_range.high)/2),c))

    melody_rng=track_rng(p.seed,'Melody','motif')
    variation_rng=track_rng(p.seed,'Melody','variation')
    rhythm_rng=track_rng(p.seed,'Melody','rhythm')
    # A recognizable eight-event motif follows a bounded random walk, not a fixed bank.
    motif=[0]
    for _ in range(7):
        motif.append(max(-2,min(5,motif[-1]+melody_rng.choice([-2,-1,1,2]))))
    rhythms={'sparse':[0,2], 'balanced':[0,1,2.5,3], 'busy':[0,.5,1,1.5,2,2.5,3,3.5]}
    previous_chord=None
    melody_events=[]
    melody_targets=[]
    for bar in range(p.bars):
        d=harmony[bar]
        if 'Chords' in s.enabled_tracks:
            chord=voices(d,previous_chord)
            previous_chord=chord
            # Re-articulate per bar; harmonic changes follow the chosen progression rate.
            for i,pitch in enumerate(chord):
                offset=i*s.chord_spread_ms*p.bpm/60000
                add('Chords',pitch,bar*4+offset,3.85-offset,0)
        if 'Bass' in s.enabled_tracks:
            bass=fit(d,s.bass_range)
            bass_rhythm=[(0,3.7)] if s.bass_mode=='sustained' else ([(0,1.25),(1.75,.6),(3, .7)] if p.style=='trap' else [(0,1.7),(2.5,1.1)])
            for i,(beat,length) in enumerate(bass_rhythm):
                pitch=bass
                # Fifth adds chordal motion; last pickup leads to the next root.
                if s.bass_mode=='rhythmic' and i>0:
                    target=d+4
                    if i==len(bass_rhythm)-1 and bar+1<p.bars and harmony[bar+1]!=d:
                        target=harmony[bar+1]-1
                    pitch=fit(target,s.bass_range,bass)
                add('Bass',pitch,bar*4+beat,length,6 if i==0 else -4)
        if 'Melody' in generated_tracks:
            positions=rhythms[p.density]
            emitted=[(i,beat) for i,beat in enumerate(positions) if not (bar%4==3 and i==1)]
            last_event=emitted[-1][0]
            for i,beat in emitted:
                step=motif[(i+(bar%2)*4)%8]
                if bar>=2 and variation_rng.random()<s.motif_variation/100:
                    step+=variation_rng.choice([-2,-1,1,2])
                phase=(bar%4)/3
                contour={'balanced':0,'ascending':round(phase*4),'descending':round((1-phase)*4),'arch':round((1-abs(2*phase-1))*4)}[s.contour]
                target_degree=d+step+contour
                if i==0 and p.style=='soul':
                    target_degree=d+2
                if s.phrase_ending=='tonic' and bar==p.bars-1 and i==last_event:
                    target_degree=0
                tonic=s.phrase_ending=='tonic' and bar==p.bars-1 and i==last_event
                anchor=d if beat in (0,2) else False
                melody_targets.append((target_degree,anchor,contour,tonic))
                sync=.25 if beat%1==0 and i>0 and rhythm_rng.random()<s.syncopation/100 else 0
                length={'sparse':1.5,'balanced':.65,'busy':.35}[p.density]
                if s.phrase_ending=='tonic' and bar==p.bars-1 and i==last_event:
                    length=4-beat-sync
                melody_events.append((bar*4+beat+sync,length,8 if beat in (0,2) else -3))
        if 'Drums' in s.enabled_tracks:
            drum_rng=track_rng(p.seed,'Drums',f'bar:{bar}')
            kicks=[0,1.5,3.25] if p.style=='trap' else [0,2.5]
            if bar%4==2 and drum_rng.random()>.5:
                kicks.append(3.5)
            for beat in kicks:
                add('Drums',36,bar*4+beat,.12,15)
            for beat in ([2] if s.drum_feel=='half-time' else [1,3]):
                add('Drums',38,bar*4+beat,.12,8)
            subdivision=.25 if s.hat_subdivision=='sixteenth' else .5
            for i in range(round(4/subdivision)):
                # Phrase-end breath and a short roll, rather than constant hats.
                beat=i*subdivision
                if s.drum_fills and bar%4==3 and beat>=3:
                    continue
                add('Drums',42,bar*4+beat,.06,-12 if i%2 else -4)
            if s.drum_fills and bar%4==3:
                for i,beat in enumerate([3,3.25,3.5,3.75]):
                    add('Drums',42,bar*4+beat,.06,-14+i*3)
                add('Drums',38,bar*4+3.5,.1,-22)
    if melody_targets:
        for pitch,(start,length,accent) in zip(melodic_path(p,melody_targets),melody_events):
            add('Melody',pitch,start,length,accent)
    if 'Countermelody' in s.enabled_tracks:
        lead=context_notes if context_notes is not None else notes
        lead=[n for n in lead if n['track']=='Melody']
        previous=None
        for bar,d in enumerate(harmony):
            positions=[1,3] if s.counter_mode=='parallel' else ([.5,1,2.5,3.5] if bar%2 else [.75,2,3.5])
            for beat in positions:
                start=bar*4+beat
                if s.counter_mode=='response':
                    # Reserve room for groove jitter on either part; keep responses in lead rests.
                    margin=(s.timing_ms+2)*p.bpm/60000
                    swung_start=start+((s.swing/100-.5) if beat%1==.5 else 0)
                    if any(n['start']<swung_start+.3+margin and n['start']+n['duration']>swung_start-margin for n in lead):
                        continue
                # Chord tones and a separate register/velocity keep the response supportive.
                pitch=choose_pitch(p,d+2,s.countermelody_range,previous,anchor=d)
                sounding=[n['pitch'] for n in lead if n['start']<=start<n['start']+n['duration']]
                if sounding and pitch in sounding:
                    alternatives=[n for n in range(s.countermelody_range.low,s.countermelody_range.high+1)
                                  if n%12 in chord_classes(p,d) and n not in sounding
                                  and (previous is None or abs(n-previous)<=s.max_melodic_leap)]
                    if alternatives: pitch=min(alternatives,key=lambda n:abs(n-pitch))
                previous=pitch
                add('Countermelody',pitch,start,.3,-3)
        if not any(n['track']=='Countermelody' for n in notes):
            raise ValueError('No room for a response counter-melody. Use parallel mode or reduce lead density.')
    notes=[n for n in notes if n['track'] in s.enabled_tracks]
    if len(notes)>MAX_NOTES:
        raise ValueError('Composition exceeds the 50,000 note budget.')
    cleaned=[]
    by_voice={}
    mono={}
    for n in sorted(notes,key=lambda n:(n['start'],n['track'],n['pitch'])):
        key=(n['track'],n['pitch'])
        prior=by_voice.get(key)
        if prior and prior['start']==n['start']:
            prior['velocity']=max(prior['velocity'],n['velocity'])
            continue
        if n['track'] in ('Melody','Bass','Countermelody'):
            prior=mono.get(n['track'])
            if prior and prior['start']==n['start']:
                continue
            mono[n['track']]=n
        if prior and prior['start']+prior['duration']>n['start']:
            prior['duration']=n['start']-prior['start']
        by_voice[key]=n
        cleaned.append(n)
    return cleaned
