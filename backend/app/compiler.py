import re

from .models import CompileResponse, DirectorProgram, EventFilter, EventType, PitchRegion


DEFAULT = "Alert me when East United wins possession in the attacking third three times within five minutes."


def compile_intent(instruction: str) -> CompileResponse:
    """Safe offline compiler used when no remote structured-output provider is configured."""
    text = instruction.strip()
    lower = text.lower()
    team_id = "north" if "north" in lower else "east"

    if re.search(r"left.?back|space behind|formation|offside line", lower):
        return CompileResponse(
            status="unsupported",
            original_instruction=text,
            message="This request requires continuous player-position data that is not present in the event stream.",
            suggested_instruction=DEFAULT,
        )

    if re.search(r"recover|wins possession", lower) and "shot" in lower:
        program = DirectorProgram(
            name="Recovery to shot sequence",
            operator="ORDERED_SEQUENCE",
            sequence=[
                EventFilter(event_type=EventType.POSSESSION_RECOVERY, team_id=team_id),
                EventFilter(event_type=EventType.SHOT, team_id=team_id),
            ],
            sequence_max_gap_seconds=15,
        )
    elif "shot" in lower and "player 7" in lower:
        program = DirectorProgram(
            name="Player 7 shot watch",
            operator="EVENT_MATCH",
            filter=EventFilter(event_type=EventType.SHOT, player_id="player_7"),
            trigger_mode="EVERY_MATCH",
            cooldown_seconds=0,
        )
    elif "shot" in lower and re.search(r"three|\b3\b|at least", lower):
        program = DirectorProgram(
            name="Shot surge",
            operator="COUNT_THRESHOLD",
            filter=EventFilter(event_type=EventType.SHOT),
            window_seconds=300,
            threshold=3,
        )
    elif re.search(r"recover|wins possession", lower):
        program = DirectorProgram(
            name="Attacking-third recoveries",
            operator="COUNT_THRESHOLD",
            filter=EventFilter(
                event_type=EventType.POSSESSION_RECOVERY,
                team_id=team_id,
                pitch_region=PitchRegion.ATTACKING_THIRD,
            ),
            window_seconds=300,
            threshold=3,
            cooldown_seconds=60,
        )
    else:
        return CompileResponse(
            status="clarification_required",
            original_instruction=text,
            message="The request could not be mapped to the supported event fields.",
            suggested_instruction=DEFAULT,
        )

    return CompileResponse(status="valid", original_instruction=text, program=program)
