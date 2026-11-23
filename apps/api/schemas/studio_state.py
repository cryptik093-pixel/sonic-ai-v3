"""Canonical, side-effect-free browser-studio state contract.

This experimental module does not alter the desktop Workbench or its SQLite
models. The server, not untrusted clients, supplies owner_id and workspace_id.
Timeline positions are integer ticks to prevent cumulative floating-point drift.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator

TICKS_PER_QUARTER = 960


class StudioModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class TimeSignature(StudioModel):
    numerator: int = Field(default=4, ge=1, le=16)
    denominator: Literal[1, 2, 4, 8, 16] = 4


class MidiNote(StudioModel):
    id: UUID
    start_tick: int = Field(ge=0)
    duration_ticks: int = Field(gt=0)
    pitch: int = Field(ge=0, le=127)
    velocity: int = Field(ge=1, le=127)
    channel: int = Field(default=0, ge=0, le=15)


class AudioRegion(StudioModel):
    kind: Literal["audio"] = "audio"
    id: UUID
    asset_id: UUID  # references existing workbench_assets.id after migration
    start_tick: int = Field(ge=0)
    duration_ticks: int = Field(gt=0)
    source_offset_frames: int = Field(default=0, ge=0)
    playback_rate: FiniteFloat = Field(default=1.0, gt=0, le=16)
    gain_db: FiniteFloat = Field(default=0.0, ge=-90, le=24)
    source_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


class MidiRegion(StudioModel):
    kind: Literal["midi"] = "midi"
    id: UUID
    start_tick: int = Field(ge=0)
    duration_ticks: int = Field(gt=0)
    notes: tuple[MidiNote, ...] = ()

    @model_validator(mode="after")
    def notes_fit_inside_region(self):
        ids: set[UUID] = set()
        for note in self.notes:
            if note.id in ids:
                raise ValueError("MIDI note IDs must be unique within a region")
            if note.start_tick + note.duration_ticks > self.duration_ticks:
                raise ValueError("MIDI notes must end within the region duration")
            ids.add(note.id)
        return self


Region = Annotated[AudioRegion | MidiRegion, Field(discriminator="kind")]


class Effect(StudioModel):
    id: UUID
    processor_id: str = Field(min_length=1, max_length=120, pattern=r"^[a-zA-Z0-9_.:-]+$")
    enabled: bool = True
    parameters: dict[str, FiniteFloat] = Field(default_factory=dict, max_length=128)
    version: str = Field(default="1", min_length=1, max_length=64)


class AutomationPoint(StudioModel):
    tick: int = Field(ge=0)
    value: FiniteFloat
    curve: Literal["step", "linear"] = "linear"


class AutomationLane(StudioModel):
    id: UUID
    target: Literal["gain_db", "pan", "plugin_parameter"]
    effect_id: UUID | None = None
    parameter: str | None = Field(default=None, max_length=120)
    points: tuple[AutomationPoint, ...] = ()

    @model_validator(mode="after")
    def valid_target_and_timing(self):
        if self.target == "plugin_parameter":
            if self.effect_id is None or not self.parameter:
                raise ValueError("plugin automation requires effect_id and parameter")
        elif self.effect_id is not None or self.parameter is not None:
            raise ValueError("track automation cannot target a plugin parameter")
        ticks = [point.tick for point in self.points]
        if ticks != sorted(set(ticks)):
            raise ValueError("automation ticks must be strictly increasing")
        if self.target == "pan" and any(not -1 <= p.value <= 1 for p in self.points):
            raise ValueError("pan automation must stay between -1 and 1")
        if self.target == "gain_db" and any(not -90 <= p.value <= 24 for p in self.points):
            raise ValueError("gain automation exceeds supported range")
        return self


class StudioTrack(StudioModel):
    id: UUID
    name: str = Field(min_length=1, max_length=120)
    kind: Literal["audio", "midi", "bus"]
    gain_db: FiniteFloat = Field(default=0.0, ge=-90, le=24)
    pan: FiniteFloat = Field(default=0.0, ge=-1, le=1)
    muted: bool = False
    soloed: bool = False
    output_track_id: UUID | None = None  # None => master; otherwise route to bus
    regions: tuple[Region, ...] = ()
    effects: tuple[Effect, ...] = ()
    automation: tuple[AutomationLane, ...] = ()

    @model_validator(mode="after")
    def validate_track(self):
        if self.kind == "bus" and self.regions:
            raise ValueError("bus tracks cannot contain audio or MIDI regions")
        if any(region.kind != self.kind for region in self.regions):
            raise ValueError("region kind must match track kind")
        if self.output_track_id == self.id:
            raise ValueError("a track cannot route into itself")
        if len({r.id for r in self.regions}) != len(self.regions):
            raise ValueError("region IDs must be unique per track")
        effects = {e.id for e in self.effects}
        if len(effects) != len(self.effects):
            raise ValueError("effect IDs must be unique per track")
        if len({lane.id for lane in self.automation}) != len(self.automation):
            raise ValueError("automation IDs must be unique per track")
        if any(l.target == "plugin_parameter" and l.effect_id not in effects for l in self.automation):
            raise ValueError("automation references a missing effect")
        return self


class StudioState(StudioModel):
    schema_version: Literal["sonic.studio-state/1.0"] = "sonic.studio-state/1.0"
    project_id: int = Field(gt=0)  # existing projects.id, not a second projects table
    owner_id: str = Field(min_length=1, max_length=80)
    workspace_id: str = Field(min_length=1, max_length=80)
    revision: int = Field(default=0, ge=0)
    bpm: FiniteFloat = Field(default=120.0, ge=40, le=240)
    time_signature: TimeSignature = Field(default_factory=TimeSignature)
    ticks_per_quarter: Literal[960] = TICKS_PER_QUARTER
    sample_rate: Literal[44100, 48000, 88200, 96000, 192000] = 48000
    master_gain_db: FiniteFloat = Field(default=0.0, ge=-90, le=24)
    tracks: tuple[StudioTrack, ...] = ()
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_references(self):
        if self.updated_at.tzinfo is None or self.updated_at.utcoffset() is None:
            raise ValueError("updated_at must carry a timezone")
        by_id = {t.id: t for t in self.tracks}
        if len(by_id) != len(self.tracks):
            raise ValueError("track IDs must be unique")
        if len({r.id for t in self.tracks for r in t.regions}) != sum(len(t.regions) for t in self.tracks):
            raise ValueError("region IDs must be unique across all tracks")
        for track in self.tracks:
            destination = track.output_track_id
            if destination is not None and (destination not in by_id or by_id[destination].kind != "bus"):
                raise ValueError("tracks must route only to an existing bus or master")
            visited = {track.id}
            while destination is not None:
                if destination in visited:
                    raise ValueError("audio routing contains a cycle")
                visited.add(destination)
                destination = by_id[destination].output_track_id
        return self
