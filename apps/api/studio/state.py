"""Typed, revisioned local studio state. Model responses never replace this object directly."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

class Project(StrictModel):
    id: str = Field(min_length=1, max_length=80)
    bpm: float = Field(ge=30, le=300)
    timeSignature: Literal["4/4"] = "4/4"
    sampleRate: Literal[44100, 48000, 96000] = 48000

class Note(StrictModel):
    note: str = Field(pattern=r"^[A-G](?:#|b)?[0-8]$")
    time: float = Field(ge=0, le=86400)
    duration: float = Field(gt=0, le=86400)
    velocity: float = Field(ge=0, le=1)

class Region(StrictModel):
    id: str = Field(min_length=1, max_length=80)
    startTime: float = Field(ge=0, le=86400)
    duration: float = Field(gt=0, le=86400)
    offset: float = Field(default=0, ge=0)
    audioUrl: str | None = Field(default=None, max_length=2048)
    notes: list[Note] = Field(default_factory=list, max_length=4096)

    @model_validator(mode="after")
    def notes_fit(self):
        if any(n.time + n.duration > self.duration + 1e-8 for n in self.notes):
            raise ValueError("MIDI note extends beyond its region")
        return self

class Bitcrusher(StrictModel):
    id: str = Field(min_length=1, max_length=80)
    type: Literal["bitcrusher"] = "bitcrusher"
    bypass: bool = False
    bits: int = Field(default=8, ge=1, le=16)
    reduction: float = Field(default=0.5, gt=0, le=1)

class Track(StrictModel):
    id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=120)
    type: Literal["audio", "midi"]
    volume: float = Field(default=0.7, ge=0, le=1)
    pan: float = Field(default=0, ge=-1, le=1)
    isMuted: bool = False
    isSoloed: bool = False
    pluginChain: list[Bitcrusher] = Field(default_factory=list, max_length=16)
    regions: list[Region] = Field(default_factory=list, max_length=256)

class StudioState(StrictModel):
    schemaVersion: Literal["sonic.studio/1"] = "sonic.studio/1"
    revision: int = Field(default=0, ge=0)
    project: Project
    tracks: list[Track] = Field(max_length=64)

    @model_validator(mode="after")
    def unique_ids(self):
        identifiers = [t.id for t in self.tracks]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Duplicate track ID")
        region_ids = [r.id for t in self.tracks for r in t.regions]
        if len(region_ids) != len(set(region_ids)):
            raise ValueError("Duplicate region ID")
        return self

def starter_session() -> StudioState:
    """Non-customer synthetic MIDI fixture; closing the socket discards this state."""
    return StudioState.model_validate({
        "project": {"id": "sonic-demo", "bpm": 128, "sampleRate": 48000},
        "tracks": [
            {"id": "drums", "name": "Drums", "type": "midi", "volume": 0.6,
             "regions": [{"id": "drum-verse", "startTime": 0, "duration": 7.5,
                          "notes": [{"note": "C2", "time": i, "duration": 0.14, "velocity": 0.5} for i in range(0, 8)]}],
             "pluginChain": [{"id": "crush-drums", "bits": 8, "reduction": 0.5}]},
            {"id": "bass", "name": "Bass Synth", "type": "midi", "volume": 0.45,
             "regions": [{"id": "bass-verse", "startTime": 0, "duration": 8,
                          "notes": [{"note": "A2", "time": 0, "duration": 2, "velocity": 0.7},
                                    {"note": "C3", "time": 2, "duration": 2, "velocity": 0.7},
                                    {"note": "E3", "time": 4, "duration": 2, "velocity": 0.7},
                                    {"note": "A2", "time": 6, "duration": 2, "velocity": 0.7}]}]},
        ],
    })
