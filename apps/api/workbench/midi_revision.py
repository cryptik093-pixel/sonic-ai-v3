"""Resolve an immutable parent-linked revision with exact locked note records."""
import copy
from .schemas import MidiCommand,MidiRevisionCommand,StudioSettings
from .midi_studio import ENGINE, compose_studio
from .models import OWNER,WORKSPACE


def resolve_revision(parent: dict, command: MidiRevisionCommand) -> tuple[MidiCommand,list[dict],dict]:
    if parent.get('id')!=str(command.parent_run_id) or parent.get('status')!='succeeded' or parent.get('kind')!='midi':
        raise ValueError('Choose a completed MIDI parent run.')
    if parent.get('owner_id')!=OWNER or parent.get('workspace_id')!=WORKSPACE:
        raise ValueError('Parent run is not in this workspace.')
    patch=copy.deepcopy(command.settings_patch)
    allowed={'title','key','scale','style','bpm','bars','density','prompt','interpretation_method','settings'}
    if set(patch)-allowed:
        raise ValueError('Revision patch contains unsupported or ownership fields.')
    source=copy.deepcopy(parent.get('result',{}).get('resolved_settings') or parent['request'])
    original=copy.deepcopy(source)
    legacy=source.get('settings') is None
    if legacy and not isinstance(patch.get('settings'),dict):
        raise ValueError('Legacy parents require an explicit settings v2 upgrade.')
    old_tracks=(source.get('settings') or {}).get('enabled_tracks',['Melody','Chords','Bass','Drums'])
    preserved=[t for t in old_tracks if t not in command.regenerate_tracks]
    for name in ('key','scale','bpm','bars'):
        if preserved and name in patch and patch[name]!=source[name]:
            raise ValueError(f'Unlock all parent tracks before changing {name}.')
    settings=copy.deepcopy(source.get('settings') or {})
    # Earlier engines never changed the last chord; retain that timeline on partial upgrades.
    if 'cadence' not in settings:
        settings['cadence']='loop'
    original.setdefault('settings',None)
    before_settings=copy.deepcopy(settings)
    settings_patch=patch.pop('settings',{})
    if not isinstance(settings_patch,dict):
        raise ValueError('Revision settings must be an object.')
    for field in settings_patch:
        track=next((t for t in old_tracks if field.startswith(t.lower()+'_')),None)
        if track in preserved:
            raise ValueError(f'Unlock {track} before changing {field}.')
    for name,value in settings_patch.items():
        if isinstance(value,dict) and isinstance(settings.get(name),dict):
            settings[name]={**settings[name],**value}
        else:settings[name]=value
    source.update(patch)
    source.update(settings=settings,seed=command.seed,request_id=str(command.request_id),project_id=parent.get('project_id'))
    resolved=MidiCommand.model_validate(source)
    enabled=resolved.settings.enabled_tracks
    if any(t not in enabled for t in preserved) or any(t not in enabled for t in command.regenerate_tracks):
        raise ValueError('Preserved and regenerated tracks must remain enabled.')
    if any(t not in old_tracks and t not in command.regenerate_tracks for t in enabled):
        raise ValueError('Select every newly enabled track for regeneration.')
    dependencies={
        'progression':{'Melody','Chords','Bass','Countermelody'},'progression_rate':{'Melody','Chords','Bass','Countermelody'},
        'chord_type':{'Chords'},'voicing':{'Chords'},'smooth_voice_leading':{'Chords'},'chord_spread_ms':{'Chords'},
        'contour':{'Melody'},'motif_variation':{'Melody'},'syncopation':{'Melody'},'phrase_ending':{'Melody'},
        'cadence':{'Melody','Chords','Bass','Countermelody'},
        'max_melodic_leap':{'Melody','Countermelody'},'counter_mode':{'Countermelody'},'drum_fills':{'Drums'},
        'bass_mode':{'Bass'},'drum_feel':{'Drums'},'hat_subdivision':{'Drums'},
        'swing':set(old_tracks),'timing_ms':set(old_tracks),'velocity_variation':set(old_tracks),
    }
    if 'Countermelody' in preserved and 'Melody' in command.regenerate_tracks and resolved.settings.counter_mode=='response':
        raise ValueError('Unlock Countermelody when changing its response lead.')
    before=StudioSettings.model_validate(before_settings).model_dump(mode='json')
    after=resolved.settings.model_dump(mode='json')
    for field,affected in dependencies.items():
        locked=set(preserved)&affected
        if locked and before[field]!=after[field]:
            raise ValueError(f'Unlock {", ".join(sorted(locked))} before changing {field}.')
    for field,affected in [('density',{'Melody'}),('style',set(old_tracks))]:
        if set(preserved)&affected and original[field]!=getattr(resolved,field):
            raise ValueError(f'Unlock {", ".join(sorted(set(preserved)&affected))} before changing {field}.')
    # Compose only the selected tracks so locked tracks need no regenerated voicing feasibility.
    selected=resolved.model_copy(update={'settings':resolved.settings.model_copy(update={'enabled_tracks':command.regenerate_tracks})})
    context=parent['result']['notes'] if 'Melody' in preserved else None
    generated=compose_studio(selected,context_notes=context)
    locked=copy.deepcopy([n for n in parent['result']['notes'] if n['track'] in preserved])
    notes=generated+locked
    inherited=parent['result'].get('track_generation_state') or {t:{'source_run_id':parent['id'],'engine':'local_composition_v1' if legacy else parent['result'].get('engine','local_composition_v2'),'parameters':original} for t in old_tracks}
    states={t:copy.deepcopy(inherited[t]) for t in preserved}
    for t in command.regenerate_tracks:
        states[t]={'source_run_id':None,'engine':ENGINE,'parameters':resolved.model_dump(mode='json')}
    metadata={'track_generation_state':states,'parent_run_id':parent['id'],'changed_settings':command.settings_patch,'regenerated_tracks':command.regenerate_tracks,
              'preserved_tracks':preserved,'legacy_upgrade':legacy}
    return resolved,notes,metadata
