from app.compiler import compile_intent
from app.data import demo_events
from app.engine import replay


def test_count_rule_triggers_once_with_grounded_evidence():
    program = compile_intent("East United wins possession in the attacking third three times within five minutes").program
    insights = replay(program, demo_events())
    assert len(insights) == 1
    assert insights[0].trigger_time_seconds == 232
    assert insights[0].evidence_event_ids == ["e01", "e03", "e05"]


def test_player_shot_rule_triggers_for_every_matching_shot():
    program = compile_intent("Follow every shot involving Player 7").program
    insights = replay(program, demo_events())
    assert [item.evidence_event_ids for item in insights] == [["e02"], ["e04"], ["e06"]]


def test_sequence_rule_uses_order_and_gap():
    program = compile_intent("Tell me when East United recovers possession and takes a shot within 15 seconds").program
    insights = replay(program, demo_events())
    assert len(insights) == 2
    assert insights[0].evidence_event_ids == ["e01", "e02"]
    assert insights[1].evidence_event_ids == ["e05", "e06"]
