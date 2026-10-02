from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Command(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    request_id: UUID = Field(default_factory=uuid4)
    project_id: int | None = Field(default=None, gt=0)


TrackName = Literal['Melody', 'Chords', 'Bass', 'Drums', 'Countermelody']


class PitchRange(BaseModel):
    model_config = ConfigDict(extra='forbid')
    low: int = Field(ge=0, le=127)
    high: int = Field(ge=0, le=127)

    @model_validator(mode='after')
    def ordered(self):
        if self.low > self.high:
            raise ValueError('Pitch range lower bound must not exceed upper bound.')
        return self


class StudioSettings(BaseModel):
    model_config = ConfigDict(extra='forbid')
    version: Literal[2] = 2
    enabled_tracks: list[TrackName] = Field(default_factory=lambda: ['Melody','Chords','Bass','Drums'], min_length=1, max_length=5)
    progression: list[int] | None = Field(default=None, min_length=1, max_length=16)
    progression_rate: Literal[1, 2, 4] = 2
    chord_type: Literal['triad','seventh','ninth'] = 'triad'
    voicing: Literal['close','open'] = 'close'
    smooth_voice_leading: bool = True
    melody_range: PitchRange = Field(default_factory=lambda: PitchRange(low=60, high=88))
    chords_range: PitchRange = Field(default_factory=lambda: PitchRange(low=45, high=79))
    bass_range: PitchRange = Field(default_factory=lambda: PitchRange(low=24, high=47))
    countermelody_range: PitchRange = Field(default_factory=lambda: PitchRange(low=60, high=79))
    countermelody_velocity: int = Field(default=62, ge=1, le=127)
    cadence: Literal['resolve', 'loop'] = 'resolve'
    max_melodic_leap: int = Field(default=7, ge=3, le=12)
    counter_mode: Literal['response', 'parallel'] = 'response'
    drum_fills: bool = True
    contour: Literal['balanced','ascending','descending','arch'] = 'balanced'
    motif_variation: int = Field(default=25, ge=0, le=100)
    syncopation: int = Field(default=30, ge=0, le=100)
    swing: int = Field(default=50, ge=50, le=67)
    timing_ms: int = Field(default=8, ge=0, le=30)
    velocity_variation: int = Field(default=6, ge=0, le=20)
    melody_velocity: int = Field(default=80, ge=1, le=127)
    chords_velocity: int = Field(default=65, ge=1, le=127)
    bass_velocity: int = Field(default=88, ge=1, le=127)
    drums_velocity: int = Field(default=75, ge=1, le=127)
    chord_spread_ms: int = Field(default=15, ge=0, le=40)
    bass_mode: Literal['sustained','rhythmic'] = 'rhythmic'
    drum_feel: Literal['half-time','backbeat'] = 'half-time'
    hat_subdivision: Literal['eighth','sixteenth'] = 'eighth'
    phrase_ending: Literal['tonic','open'] = 'tonic'

    @model_validator(mode='after')
    def valid_lists(self):
        if len(set(self.enabled_tracks)) != len(self.enabled_tracks):
            raise ValueError('Choose each track only once.')
        if self.progression and any(not 1 <= d <= 7 for d in self.progression):
            raise ValueError('Progression degrees must be 1 through 7.')
        return self


class MidiCommand(Command):
    title: str = Field(default='Midnight Signal', min_length=1, max_length=100)
    key: Literal['C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B'] = 'C'
    scale: Literal['minor','major','dorian','harmonic_minor'] = 'minor'
    style: Literal['cloud','trap','soul'] = 'cloud'
    bpm: int = Field(default=130, ge=60, le=200)
    bars: Literal[4,8,16,32] = 8
    seed: int = Field(default=93, ge=0, le=2147483647)
    density: Literal['sparse','balanced','busy'] = 'balanced'
    prompt: str = Field(default='', max_length=2000)
    interpretation_method: Literal['manual','local_supported_instructions','cloud_settings_proposal'] = 'manual'
    settings: StudioSettings | None = None

    @model_validator(mode='before')
    @classmethod
    def aliases(cls, value):
        if isinstance(value, dict):
            value = dict(value)
            value['key'] = {'Db':'C#','D#':'Eb','Gb':'F#','G#':'Ab','A#':'Bb','Cb':'B','B#':'C'}.get(value.get('key'),value.get('key','C'))
        return value

    @model_validator(mode='after')
    def studio_length(self):
        if self.bars == 32 and self.settings is None:
            raise ValueError('32 bars requires MIDI Studio settings v2.')
        return self


class MidiRevisionCommand(Command):
    parent_run_id: UUID
    regenerate_tracks: list[TrackName] = Field(min_length=1, max_length=5)
    settings_patch: dict = Field(default_factory=dict)
    seed: int = Field(default=93, ge=0, le=2147483647)

    @model_validator(mode='after')
    def distinct(self):
        if len(set(self.regenerate_tracks)) != len(self.regenerate_tracks):
            raise ValueError('Choose each revision track only once.')
        return self


class MidiInterpretCommand(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    prompt: str = Field(min_length=1, max_length=2000)
    current: MidiCommand = Field(default_factory=lambda: MidiCommand(settings={}))
    use_cloud: bool = False
    explicit_fields: list[str] = Field(default_factory=list, max_length=60)


class MidiInterpretResult(BaseModel):
    method: Literal['local_supported_instructions','cloud_settings_proposal']
    status: Literal['ready','partial','unavailable']
    proposed_settings: dict
    unresolved: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


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
