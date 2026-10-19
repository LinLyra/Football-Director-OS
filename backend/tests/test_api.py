from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["dsl_version"] == "1.0"


def test_compile_endpoint_returns_validated_program():
    response = client.post("/api/director/compile", json={"instruction": "Follow every shot involving Player 7"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "valid"
    assert body["program"]["operator"] == "EVENT_MATCH"
