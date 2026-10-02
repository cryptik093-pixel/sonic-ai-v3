import importlib.util
from unittest.mock import patch
import pytest
from apps.api.workbench.schemas import MidiInterpretCommand, MidiCommand


def test_prompt_module_exists():
    assert importlib.util.find_spec('apps.api.workbench.midi_prompt'), 'prompt interpreter missing'


def interpret(**kw):
    from apps.api.workbench.midi_prompt import interpret_prompt
    return interpret_prompt(MidiInterpretCommand(**kw))


def test_supported_offline_and_unhandled_text():
    r=interpret(prompt='F# minor 140 bpm 16 bars sparse trap ascending melody seventh chords 60% swing unknown texture')
    p=r.proposed_settings
    assert p['key']=='F#' and p['bpm']==140 and p['bars']==16 and p['density']=='sparse' and p['style']=='trap'
    assert p['settings']['swing']==60 and p['settings']['contour']=='ascending' and p['settings']['chord_type']=='seventh'
    assert r.unresolved and r.method=='local_supported_instructions'


def test_conflicts_out_of_range_and_explicit_controls():
    r=interpret(prompt='120 bpm 150 bpm 99 bars')
    assert r.status=='partial' and r.proposed_settings['bpm']==130 and r.warnings
    r=interpret(prompt='140 bpm trap',current=MidiCommand(bpm=160,style='soul',settings={}),explicit_fields=['bpm','style'])
    assert r.proposed_settings['bpm']==160 and r.proposed_settings['style']=='soul'


def test_unknown_unicode_html_is_data():
    text='<script>écho 謎</script>'
    r=interpret(prompt=text)
    assert r.unresolved==[text] and r.status=='partial'


@pytest.mark.parametrize('answer',['not json','{"bpm":999}','{"notes":[]}', '{"settings":{"enabled_tracks":[]}}'])
def test_cloud_invalid_proposal_sanitized(monkeypatch,answer):
    monkeypatch.setenv('SONIC_OPENAI_API_KEY','fixture-key')
    with patch('apps.api.services.llm_service.LLMService.generate',return_value=answer):
        r=interpret(prompt='dark soul',use_cloud=True)
    assert r.status=='unavailable' and all('fixture-key' not in w for w in r.warnings)


def test_cloud_success_timeout_and_no_key(monkeypatch):
    r=interpret(prompt='140 bpm',use_cloud=True)
    assert r.status=='unavailable' and r.proposed_settings['bpm']==140
    monkeypatch.setenv('SONIC_OPENAI_API_KEY','fixture-key')
    with patch('apps.api.services.llm_service.LLMService.generate',return_value='{"bpm":145,"settings":{"swing":58}}'):
        r=interpret(prompt='laid back',use_cloud=True)
    assert r.status=='ready' and r.proposed_settings['bpm']==145 and r.proposed_settings['settings']['swing']==58
    from apps.api.services.llm_service import LLMServiceError
    with patch('apps.api.services.llm_service.LLMService.generate',side_effect=LLMServiceError('provider timeout')):
        r=interpret(prompt='140 bpm',use_cloud=True)
    assert r.status=='unavailable' and r.proposed_settings['bpm']==140
