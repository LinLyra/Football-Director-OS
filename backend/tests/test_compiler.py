from app.compiler import compile_intent


def test_compiles_attacking_third_recovery_rule():
    result = compile_intent("Alert me when East United wins possession in the attacking third three times within five minutes.")
    assert result.status == "valid"
    assert result.program.operator == "COUNT_THRESHOLD"
    assert result.program.threshold == 3
    assert result.program.filter.pitch_region.value == "ATTACKING_THIRD"


def test_refuses_unobservable_tactical_claim():
    result = compile_intent("Tell me when the left-back leaves too much space behind him.")
    assert result.status == "unsupported"
    assert result.program is None
    assert "continuous player-position" in result.message


def test_requests_clarification_for_unknown_intent():
    result = compile_intent("Make this match interesting for me")
    assert result.status == "clarification_required"
