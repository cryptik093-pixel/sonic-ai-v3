"""Fast, dependency-light contract tests; no database or audio devices required."""
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from apps.api.schemas.studio_state import StudioState


def state_with(tracks, **overrides):
    return {"project_id": 1, "owner_id": "local-producer", "workspace_id": "omega-house-studio",
            "tracks": tracks, "updated_at": datetime.now(UTC), **overrides}


def track(kind="audio", **overrides):
    return {"id": str(uuid4()), "name": "Track 1", "kind": kind, **overrides}


def test_empty_state_roundtrips_without_mutating_old_workbench():
    initial = StudioState.model_validate(state_with([]))
    assert initial.revision == 0
    assert initial.ticks_per_quarter == 960
    assert StudioState.model_validate_json(initial.model_dump_json()) == initial


def test_valid_audio_and_midi_with_effect_and_automation():
    fx = str(uuid4())
    tracks = [
        track(regions=[{"kind": "audio", "id": str(uuid4()), "asset_id": str(uuid4()),
                        "start_tick": 0, "duration_ticks": 3840}],
              effects=[{"id": fx, "processor_id": "builtin.bitcrusher", "parameters": {"bits": 12.0}}],
              automation=[{"id": str(uuid4()), "target": "plugin_parameter", "effect_id": fx,
                           "parameter": "bits", "points": [{"tick": 0, "value": 12}, {"tick": 960, "value": 8}]}]),
        track("midi", regions=[{"kind": "midi", "id": str(uuid4()), "start_tick": 0,
                                "duration_ticks": 960, "notes": [{"id": str(uuid4()),
                                "pitch": 60, "velocity": 90, "start_tick": 0, "duration_ticks": 480}]}])
    ]
    state = StudioState.model_validate(state_with(tracks))
    assert state.tracks[1].regions[0].notes[0].pitch == 60


def test_duplicate_track_ids_are_rejected():
    a = track()
    with pytest.raises(ValidationError, match="track IDs must be unique"):
        StudioState.model_validate(state_with([a, a]))


def test_duplicate_regions_across_tracks_are_rejected():
    region = {"kind": "audio", "id": str(uuid4()), "asset_id": str(uuid4()),
              "start_tick": 0, "duration_ticks": 960}
    with pytest.raises(ValidationError, match="region IDs must be unique across"):
        StudioState.model_validate(state_with([track(regions=[region]), track(regions=[region])]))


def test_midi_note_outside_clip_is_rejected():
    invalid = track("midi", regions=[{"kind": "midi", "id": str(uuid4()), "start_tick": 0,
                                       "duration_ticks": 100, "notes": [{"id": str(uuid4()),
                                           "start_tick": 90, "duration_ticks": 20,
                                           "pitch": 60, "velocity": 80}]}])
    with pytest.raises(ValidationError, match="within the region"):
        StudioState.model_validate(state_with([invalid]))


def test_cross_track_mismatch_and_unknown_routing_fail():
    with pytest.raises(ValidationError, match="region kind"):
        StudioState.model_validate(state_with([track("midi", regions=[{"kind": "audio", "id": str(uuid4()),
            "asset_id": str(uuid4()), "start_tick": 0, "duration_ticks": 960}])]))
    with pytest.raises(ValidationError, match="existing bus"):
        StudioState.model_validate(state_with([track(output_track_id=str(uuid4()))]))


def test_bus_routing_cycle_is_rejected():
    a, b = str(uuid4()), str(uuid4())
    with pytest.raises(ValidationError, match="cycle"):
        StudioState.model_validate(state_with([
            track("bus", id=a, output_track_id=b), track("bus", id=b, output_track_id=a)]))


def test_invalid_automation_values_and_order_rejected():
    bad_track = track(automation=[{"id": str(uuid4()), "target": "pan", "points": [
        {"tick": 960, "value": 0}, {"tick": 0, "value": 0.1}]}])
    with pytest.raises(ValidationError, match="strictly increasing"):
        StudioState.model_validate(state_with([bad_track]))
    with pytest.raises(ValidationError, match="pan automation"):
        StudioState.model_validate(state_with([track(automation=[{
            "id": str(uuid4()), "target": "pan", "points": [{"tick": 0, "value": 3}]}])]))


def test_nan_infinity_and_unknown_fields_rejected():
    for bpm in (float("nan"), float("inf"), -1):
        with pytest.raises(ValidationError):
            StudioState.model_validate(state_with([], bpm=bpm))
    with pytest.raises(ValidationError, match="Extra inputs"):
        StudioState.model_validate({**state_with([]), "admin": True})


def test_naive_timestamp_rejected():
    with pytest.raises(ValidationError, match="timezone"):
        StudioState.model_validate(state_with([], updated_at=datetime(2026, 10, 14)))
