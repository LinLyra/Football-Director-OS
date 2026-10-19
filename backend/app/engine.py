from collections import deque
from typing import Deque, Dict, List, Optional

from .models import DirectorProgram, EventFilter, EvidenceValue, MatchEvent, TriggeredInsight


def _region(event: MatchEvent) -> Optional[str]:
    if event.location_x is None:
        return None
    if event.location_x >= 66.7:
        return "ATTACKING_THIRD"
    if event.location_x <= 33.3:
        return "DEFENSIVE_THIRD"
    return "MIDDLE_THIRD"


def _matches(event: MatchEvent, condition: EventFilter) -> bool:
    return (
        event.event_type == condition.event_type
        and (condition.team_id is None or event.team_id == condition.team_id)
        and (condition.player_id is None or event.player_id == condition.player_id)
        and (condition.pitch_region is None or _region(event) == condition.pitch_region.value)
    )


class TemporalRuleEngine:
    """Deterministic single-program engine with replay-safe state."""

    def __init__(self, program: DirectorProgram):
        self.program = program
        self.events: Deque[MatchEvent] = deque()
        self.condition_active = False
        self.last_trigger_time: Optional[int] = None
        self.insight_counter = 0

    def _cooldown_allows(self, timestamp: int) -> bool:
        return self.last_trigger_time is None or timestamp - self.last_trigger_time >= self.program.cooldown_seconds

    def _emit(self, event: MatchEvent, evidence: List[MatchEvent], values: Dict[str, object]) -> TriggeredInsight:
        self.insight_counter += 1
        self.last_trigger_time = event.event_time_seconds
        return TriggeredInsight(
            id=f"insight_{self.insight_counter:03d}",
            program_name=self.program.name,
            trigger_time_seconds=event.event_time_seconds,
            evidence_event_ids=[item.id for item in evidence],
            computed_values=[EvidenceValue(key=key, value=value) for key, value in values.items()],
        )

    def process(self, event: MatchEvent) -> Optional[TriggeredInsight]:
        self.events.append(event)

        if self.program.operator == "EVENT_MATCH":
            if _matches(event, self.program.filter) and self._cooldown_allows(event.event_time_seconds):
                return self._emit(event, [event], {"event_type": event.event_type.value})
            return None

        if self.program.operator == "COUNT_THRESHOLD":
            cutoff = event.event_time_seconds - self.program.window_seconds
            while self.events and self.events[0].event_time_seconds < cutoff:
                self.events.popleft()
            evidence = [item for item in self.events if _matches(item, self.program.filter)]
            satisfied = len(evidence) >= self.program.threshold
            should_emit = satisfied and (self.program.trigger_mode == "EVERY_MATCH" or not self.condition_active)
            self.condition_active = satisfied
            if should_emit and self._cooldown_allows(event.event_time_seconds):
                return self._emit(event, evidence, {"count": len(evidence), "window_seconds": self.program.window_seconds})
            return None

        if self.program.operator == "ORDERED_SEQUENCE" and _matches(event, self.program.sequence[1]):
            first = next(
                (
                    item for item in reversed(self.events)
                    if item.sequence_number < event.sequence_number
                    and _matches(item, self.program.sequence[0])
                    and event.event_time_seconds - item.event_time_seconds <= self.program.sequence_max_gap_seconds
                ),
                None,
            )
            if first and self._cooldown_allows(event.event_time_seconds):
                return self._emit(
                    event,
                    [first, event],
                    {"gap_seconds": event.event_time_seconds - first.event_time_seconds},
                )
        return None


def replay(program: DirectorProgram, events: List[MatchEvent]) -> List[TriggeredInsight]:
    engine = TemporalRuleEngine(program)
    insights: List[TriggeredInsight] = []
    for event in sorted(events, key=lambda item: (item.sequence_number, item.event_time_seconds)):
        insight = engine.process(event)
        if insight:
            insights.append(insight)
    return insights
