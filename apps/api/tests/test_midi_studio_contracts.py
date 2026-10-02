import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from apps.api.workbench import schemas, midi


def test_studio_contract_exists_and_legacy_is_default():
    assert hasattr(schemas, 'StudioSettings'), 'StudioSettings missing'
    assert schemas.MidiCommand().settings is None
    assert schemas.MidiCommand(bars=32, settings={}).settings.version == 2
    with pytest.raises(ValidationError):
        schemas.MidiCommand(bars=32)


@pytest.mark.parametrize('settings', [
    {'enabled_tracks': []}, {'swing': 68}, {'timing_ms':31}, {'velocity_variation':21},
    {'progression':[0]}, {'progression':[1]*17}, {'melody_range':{'low':80,'high':60}},
    {'unknown':True}, {'melody_range':{'low':-1,'high':80}}, {'enabled_tracks':['Melody','Melody']},
])
def test_settings_bounds(settings):
    with pytest.raises(ValidationError):
        schemas.MidiCommand(settings=settings)


def test_aliases_prompt_and_revision_contract():
    assert hasattr(schemas, 'MidiRevisionCommand'), 'revision contract missing'
    assert schemas.MidiCommand(key='Db',settings={}).key == 'C#'
    with pytest.raises(ValidationError):
        schemas.MidiCommand(prompt='x'*2001,settings={})
    from uuid import uuid4
    with pytest.raises(ValidationError):
        schemas.MidiRevisionCommand(parent_run_id=uuid4(),regenerate_tracks=[])
    assert schemas.MidiInterpretCommand(prompt='130 bpm').current.settings is not None


def test_legacy_notes_match_saved_baseline():
    data=json.loads((Path(__file__).parent/'fixtures/midi_v1_notes.json').read_text())
    for fixture in data:
        assert midi.compose(schemas.MidiCommand(**fixture['parameters'])) == fixture['notes']
