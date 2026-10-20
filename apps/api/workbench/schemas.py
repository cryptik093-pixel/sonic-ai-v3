from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Command(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    request_id: UUID = Field(default_factory=uuid4)
    project_id: int | None = Field(default=None, gt=0)


class MidiCommand(Command):
    prompt: str = Field(default="", max_length=2000)
    title: str = Field(default="Midnight Signal", min_length=1, max_length=100)
    key: Literal["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"] = "C"
    scale: Literal["minor", "major", "dorian", "harmonic_minor"] = "minor"
    style: Literal["cloud", "trap", "soul"] = "cloud"
    mood: Literal["neutral", "dark", "hopeful", "dreamy", "tense", "uplifting"] = "neutral"
    bpm: int = Field(default=130, ge=60, le=200)
    bars: Literal[4, 8, 16] = 8
    seed: int = Field(default=93, ge=0, le=2147483647)
    density: Literal["sparse", "balanced", "busy"] = "balanced"


class AnalyzeCommand(Command):
    asset_id: UUID


class PackCommand(Command):
    title: str = Field(min_length=1, max_length=100)
    asset_ids: list[UUID] = Field(default_factory=list, max_length=200)
    source_run_id: UUID | None = None
    license_text: str = Field(default="", max_length=20000)
    artist: str = Field(default="Omega House Beats", min_length=1, max_length=100)

    @model_validator(mode="after")
    def needs_assets(self):
        if not self.asset_ids and self.source_run_id is None:
            raise ValueError("Select imported assets or a MIDI run to package.")
        return self


class ReleaseCommand(Command):
    pack_run_id: UUID
    audience: str = Field(default="Hip-hop and trap producers", min_length=1, max_length=200)
    price: float = Field(default=5, ge=0, le=10000, allow_inf_nan=False)
    product_url: str = Field(default="https://omega-house.online", max_length=2048)


class FocusCommand(Command):
    energy: Literal["low", "steady", "high"] = "low"
    minutes: Literal[5, 15, 30, 60] = 15
    goal: Literal["create", "finish", "release"] = "create"


class CoachCommand(Command):
    run_id: UUID
    question: str = Field(default="What is the most useful next step?", min_length=1, max_length=2000)


class FeedbackCommand(Command):
    decision: Literal["keep", "not_for_me"]
    note: str = Field(default="", max_length=500)


class FeedbackEventPayload(BaseModel):
    schema_version: Literal["sonic.workbench-feedback/1.0"] = "sonic.workbench-feedback/1.0"
    request_id: UUID
    decision: Literal["keep", "not_for_me"]
    note: str = Field(max_length=500)
