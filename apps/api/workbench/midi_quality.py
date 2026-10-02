"""Measured MIDI validity and exported state; musical quality requires listening."""
import json
import math
from collections import Counter
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5
import mido
from . import midi
from .schemas import MidiCommand
from .midi_studio import ENGINE, MAX_NOTES
from .harmony import harmonic_plan, chord_classes


def validate_notes(notes: list[dict], command: MidiCommand) -> dict:
    s=command.settings
    if s is None or not notes or len(notes)>MAX_NOTES:
        raise ValueError('Use a nonempty Studio composition within the 50,000 note budget.')
    if set(s.enabled_tracks) != {n["track"] for n in notes}:
        raise ValueError("Each enabled track must contain notes; select newly enabled tracks for regeneration.")
    voices={}
    for n in sorted(notes,key=lambda n:n['start']):
        track=n['track']
        if track not in s.enabled_tracks:
            raise ValueError('Composition contains a disabled track.')
        if not all(math.isfinite(n[k]) for k in ('pitch','start','duration','velocity')):
            raise ValueError('Composition contains non-finite notes.')
        if not (0<=n['pitch']<=127 and int(n['pitch'])==n['pitch'] and 1<=n['velocity']<=127 and int(n['velocity'])==n['velocity']):
            raise ValueError('MIDI pitches and velocities are out of range.')
        on=round(n['start']*midi.TICKS);off=round((n['start']+n['duration'])*midi.TICKS)
        if n['start']<0 or n['duration']<=0 or on<0 or off<=on or off>command.bars*4*midi.TICKS:
            raise ValueError('Notes must fit inside the arrangement with a positive tick duration.')
        key=(track,n['pitch'])
        if voices.get(key,-1)>on:
            raise ValueError('Overlapping same-pitch notes must be resolved before export.')
        voices[key]=off
        if track!='Drums':
            register=getattr(s,track.lower()+'_range')
            if not register.low<=n['pitch']<=register.high or (n['pitch']-midi.ROOTS[command.key])%12 not in midi.SCALES[command.scale]:
                raise ValueError('Pitched note is outside the selected range or scale.')
    return {'passed':True,'note_count':len(notes),'checks':['finite_notes','midi_bounds','positive_tick_duration','arrangement_bounds','scale_and_register','same_pitch_lifecycle']}


def measure_notes(notes: list[dict], command: MidiCommand) -> dict:
    melody=sorted([n for n in notes if n['track']=='Melody'],key=lambda n:n['start'])
    pitched=[n for n in notes if n['track']!='Drums']
    ranges={track:{'low':min(n['pitch'] for n in notes if n['track']==track),'high':max(n['pitch'] for n in notes if n['track']==track)} for track in sorted({n['track'] for n in notes})}
    chord_groups={}
    for n in notes:
        if n['track']=='Chords':chord_groups.setdefault(round(n['start']/4),[]).append(n['pitch'])
    # This engine articulates chords at bar boundaries; snap jittered notes to
    # the nearest nominal boundary rather than treating early notes as prior chords.
    chords=[sorted(v) for _,v in sorted(chord_groups.items())]
    movement=[sum(abs(a-b) for a,b in zip(x,y)) for x,y in zip(chords,chords[1:])]
    phrases=[]
    for start in range(0,command.bars*4,8):
        phrases.append(tuple((round(n['start']-start,3),n['pitch']) for n in melody if start<=n['start']<start+8))
    harmony=harmonic_plan(command)
    anchors=[n for n in melody if abs(n['start']-round(n['start']/2)*2)<.15]
    consonant=sum(n['pitch']%12 in chord_classes(command,harmony[min(command.bars-1,int((n['start']+.15)//4))]) for n in anchors)
    counters=[n for n in notes if n['track']=='Countermelody']
    overlap=sum(any(m['start']<n['start']+n['duration'] and m['start']+m['duration']>n['start'] for m in melody) for n in counters)
    return {'harmonic_degrees_by_bar':[d+1 for d in harmony],
            'strong_beat_melody_chord_tone_ratio':round(consonant/len(anchors),3) if anchors else None,
            'countermelody_lead_overlap_events':overlap,
            'note_count':len(notes),'pitch_ranges':ranges,'pitch_class_distribution':dict(sorted(Counter(n['pitch']%12 for n in pitched).items())),
            'notes_per_bar':round(len(notes)/command.bars,3),
            'max_melodic_leap_semitones':max([abs(a['pitch']-b['pitch']) for a,b in zip(melody,melody[1:])] or [0]),
            'adjacent_chord_movement_semitones':movement,
            'exact_two_bar_phrase_repetitions':len(phrases)-len(set(phrases))}


def export_studio(command: MidiCommand, notes: list[dict], folder: Path, provenance: dict) -> dict:
    p=command
    quality={'technical':validate_notes(notes,p),'measurements':measure_notes(notes,p),
             'interpretation':{'status':'heuristic','message':'Scale and timing checks establish MIDI validity. Musical usefulness and commercial readiness require operator review.'}}
    meta=midi.conductor(p)
    if p.scale in ('minor','major'):
        key_name=p.key+('m' if p.scale=='minor' else '')
        try:
            key_meta=mido.MetaMessage('key_signature',key=key_name)
        except ValueError:
            key_meta=None
        if key_meta is not None:
            meta=meta+[key_meta]
    end=p.bars*4*midi.TICKS
    song=mido.MidiFile(type=1,ticks_per_beat=midi.TICKS)
    song.tracks.append(mido.MidiTrack([mido.MetaMessage('track_name',name='Tempo'),*meta,mido.MetaMessage('end_of_track',time=end)]))
    tracks=[]
    for name,channel,program in midi.TRACKS + midi.STUDIO_EXTRA_TRACKS:
        if name not in p.settings.enabled_tracks:continue
        tracks.append(name)
        song.tracks.append(midi.note_track(notes,name,channel,program,end))
        part=mido.MidiFile(type=0,ticks_per_beat=midi.TICKS)
        part.tracks.append(midi.note_track(notes,name,channel,program,end,meta))
        part.save(folder/f'{name}.mid')
    prefix=f'{midi.slug(p.title)}_{p.key.replace("#","sharp")}_{p.scale}_{p.bpm}BPM'
    song.save(folder/f'{prefix}.mid')
    midi.render_preview(notes,p.bpm,p.bars,folder/'Audition.wav')
    track_state=provenance.get('revision',{}).get('track_generation_state',{}) if provenance.get('revision') else {}
    if not track_state:
        track_state={t:{'source_run_id':provenance.get('run_id'),'engine':ENGINE,'parameters':p.model_dump(mode='json')} for t in tracks}
    for t,info in track_state.items():
        if info.get('source_run_id') is None:info['source_run_id']=provenance.get('run_id')
    record={'track_generation_state':track_state,'schema_version':'2.0',**provenance,'engine_version':ENGINE,'parameters':p.model_dump(mode='json'),
            'prompt':p.prompt,'interpretation_method':p.interpretation_method,'notes':notes,'validation':quality,
            'track_ids':{t:str(uuid5(NAMESPACE_URL,f"sonic:{provenance.get('run_id','local')}:{t}")) for t in tracks},
            'instrument_state':'unspecified','preset_state':'unspecified','audition':{'derived_from':'MIDI note records','renderer':'simple_synthesis_v1'},
            'artifact_hashes':'Recorded in the owning run artifact manifest; self-hash excluded.'}
    (folder/'Composition.json').write_text(json.dumps(record,indent=2,allow_nan=False),encoding='utf-8')
    (folder/'Quality_Report.json').write_text(json.dumps(quality,indent=2,allow_nan=False),encoding='utf-8')
    (folder/'FL_Studio_Readme.md').write_text(f'# {p.title}\n\n{p.bars} bars, {p.bpm} BPM, {p.key} {p.scale}.\n\n'
        'Countermelody.mid is a separate optional pitched part. Drag individual MIDI parts into an instrument Piano Roll. Import the combined arrangement through File > Import > MIDI file. '
        'Use the tempo above. Drums use GM channel 10: 36 kick, 38 snare, 42 closed hat. Map these notes to your own instruments.\n\n'
        'Audition.wav uses simple synthesis; it is not a finished or mastered recording. Choose your own sounds in FL Studio. '
        'Composition.json preserves settings, seed, lineage and unspecified instrument/preset state. Quality_Report.json contains technical measurements.\n',encoding='utf-8')
    action='Audition the final phrase against the first phrase, then choose instruments in FL Studio and save a listening note.'
    decision={'objective':'Develop a usable composition','status':'proposed','owner':provenance.get('owner_id','local-producer'),
              'recommendation':action,'evidence':[{'kind':'validated_midi','ref':provenance.get('run_id'),'note_count':len(notes)}],
              'assumptions':['Musical quality has not been assessed by listening.'],'confidence':'high for technical validity; unassessed for musical usefulness',
              'risks':['Simple audition timbre may not represent final production.'],'next_validation':'Compare phrase identity, groove and ending using your DAW instruments.'}
    return {'title':p.title,'engine':ENGINE,'bpm':p.bpm,'key':p.key,'scale':p.scale,'bars':p.bars,'seed':p.seed,
            'note_count':len(notes),'tracks':tracks,'notes':notes,'resolved_settings':p.model_dump(mode='json'),
            'track_generation_state':track_state,'parent_run_id':provenance.get('parent_run_id'),'revision':provenance.get('revision'),
            'quality':quality,'decision_record':decision,'summary':f'{p.bars} bars with {len(tracks)} selected MIDI parts and saved composition state.',
            'next_action':action,'warnings':['Algorithmic composition; listening acceptance is pending.','Audition audio uses simple synth sounds.']}
