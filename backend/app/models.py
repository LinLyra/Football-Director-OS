from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class EventType(str, Enum):
    PASS = "PASS"
    SHOT = "SHOT"
    POSSESSION_RECOVERY = "POSSESSION_RECOVERY"
    POSSESSION_LOSS = "POSSESSION_LOSS"
    TACKLE = "TACKLE"
    PRESSURE = "PRESSURE"
    GOAL = "GOAL"
    SUBSTITUTION = "SUBSTITUTION"


class PitchRegion(str, Enum):
    DEFENSIVE_THIRD = "DEFENSIVE_THIRD"
    MIDDLE_THIRD = "MIDDLE_THIRD"
    ATTACKING_THIRD = "ATTACKING_THIRD"


class MatchEvent(BaseModel):
    id: str
    match_id: str = "match_demo_01"
    sequence_number: int = Field(ge=0)
    event_time_seconds: int = Field(ge=0, le=5_400)
    event_type: EventType
    team_id: str
    player_id: Optional[str] = None
    player_name: Optional[str] = None
    location_x: Optional[float] = Field(default=None, ge=0, le=100)
    location_y: Optional[float] = Field(default=None, ge=0, le=100)
    outcome: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EventFilter(BaseModel):
    event_type: EventType
    team_id: Optional[str] = None
    player_id: Optional[str] = None
    pitch_region: Optional[PitchRegion] = None


class DirectorProgram(BaseModel):
    dsl_version: Literal["1.0"] = "1.0"
    name: str = Field(min_length=1, max_length=80)
    operator: Literal["EVENT_MATCH", "COUNT_THRESHOLD", "ORDERED_SEQUENCE"]
    filter: Optional[EventFilter] = None
    sequence: Optional[List[EventFilter]] = None
    window_seconds: Optional[int] = Field(default=None, ge=1, le=900)
    threshold: Optional[int] = Field(default=None, ge=1, le=20)
    sequence_max_gap_seconds: Optional[int] = Field(default=None, ge=1, le=120)
    trigger_mode: Literal["EVERY_MATCH", "RISING_EDGE"] = "RISING_EDGE"
    cooldown_seconds: int = Field(default=30, ge=0, le=900)

    @model_validator(mode="after")
    def validate_operator_fields(self):
        if self.operator in {"EVENT_MATCH", "COUNT_THRESHOLD"} and not self.filter:
            raise ValueError(f"{self.operator} requires filter")
        if self.operator == "COUNT_THRESHOLD" and (not self.window_seconds or not self.threshold):
            raise ValueError("COUNT_THRESHOLD requires window_seconds and threshold")
        if self.operator == "ORDERED_SEQUENCE":
            if not self.sequence or len(self.sequence) != 2:
                raise ValueError("ORDERED_SEQUENCE requires exactly two filters")
            if not self.sequence_max_gap_seconds:
                raise ValueError("ORDERED_SEQUENCE requires sequence_max_gap_seconds")
        return self


class CompileRequest(BaseModel):
    instruction: str = Field(min_length=3, max_length=500)
    match_id: str = "match_demo_01"


class CompileResponse(BaseModel):
    status: Literal["valid", "unsupported", "clarification_required"]
    original_instruction: str
    program: Optional[DirectorProgram] = None
    message: Optional[str] = None
    suggested_instruction: Optional[str] = None
    provider: str = "deterministic-fallback"


class EvidenceValue(BaseModel):
    key: str
    value: Any


class TriggeredInsight(BaseModel):
    id: str
    program_name: str
    trigger_time_seconds: int
    evidence_event_ids: List[str]
    computed_values: List[EvidenceValue]
    verification_status: Literal["verified"] = "verified"


class ReplayRequest(BaseModel):
    program: DirectorProgram
    events: List[MatchEvent]


class ReplayResponse(BaseModel):
    insights: List[TriggeredInsight]
    processed_events: int


class ProgramCreateRequest(BaseModel):
    original_instruction: str = Field(min_length=3, max_length=500)
    program: DirectorProgram


class ProgramStatusRequest(BaseModel):
    status: Literal["active", "paused"]
