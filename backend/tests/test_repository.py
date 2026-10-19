from app.compiler import compile_intent
from app.repository import ProgramRepository


def test_program_registry_persists_status_and_version(tmp_path):
    repository = ProgramRepository(str(tmp_path / "registry.db"))
    program = compile_intent("Follow every shot involving Player 7").program
    created = repository.create("Follow every shot involving Player 7", program)
    assert created["version"] == 1
    assert created["status"] == "active"
    paused = repository.set_status(created["id"], "paused")
    assert paused["status"] == "paused"
    assert repository.list()[0]["program"]["operator"] == "EVENT_MATCH"
