from dataclasses import dataclass
from typing import Dict, List

from .compiler import compile_intent


@dataclass(frozen=True)
class BenchmarkCase:
    instruction: str
    expected_status: str
    expected_operator: str = ""


CASES = [
    BenchmarkCase("East United wins possession in the attacking third three times within five minutes", "valid", "COUNT_THRESHOLD"),
    BenchmarkCase("Follow every shot involving Player 7", "valid", "EVENT_MATCH"),
    BenchmarkCase("East United recovers possession and takes a shot within 15 seconds", "valid", "ORDERED_SEQUENCE"),
    BenchmarkCase("Notify me when there are at least three shots in five minutes", "valid", "COUNT_THRESHOLD"),
    BenchmarkCase("Tell me when the left-back leaves too much space", "unsupported"),
    BenchmarkCase("Alert me when the offside line is disorganized", "unsupported"),
    BenchmarkCase("Make it exciting", "clarification_required"),
    BenchmarkCase("Give me something interesting", "clarification_required"),
]


def run_benchmark() -> Dict:
    outcomes: List[Dict] = []
    correct = 0
    for case in CASES:
        result = compile_intent(case.instruction)
        operator = result.program.operator if result.program else ""
        passed = result.status == case.expected_status and operator == case.expected_operator
        correct += int(passed)
        outcomes.append({
            "instruction": case.instruction, "expected_status": case.expected_status,
            "actual_status": result.status, "expected_operator": case.expected_operator,
            "actual_operator": operator, "passed": passed,
        })
    return {"total": len(CASES), "correct": correct, "accuracy": correct / len(CASES), "cases": outcomes}
