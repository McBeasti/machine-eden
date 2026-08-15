"""Tests for FastAPI endpoints."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_get_state():
    r = client.get("/api/simulation/state")
    assert r.status_code == 200
    data = r.json()
    assert "world" in data
    assert "agents" in data
    assert "config" in data


def test_get_config():
    r = client.get("/api/simulation/config")
    assert r.status_code == 200
    assert "seed" in r.json()


def test_step_simulation():
    r = client.post("/api/simulation/step")
    assert r.status_code == 200
    data = r.json()
    assert "tick" in data
    assert "agents" in data
    assert "metrics" in data


def test_pause_resume():
    client.post("/api/simulation/start")
    r = client.post("/api/simulation/pause")
    assert r.status_code == 200
    assert r.json()["running"] is False


def test_reset_simulation():
    r = client.post("/api/simulation/reset", json={"seed": 99})
    assert r.status_code == 200
    assert r.json()["config"]["seed"] == 99


def test_get_agent_not_found():
    r = client.get("/api/agents/nonexistent-id")
    assert r.status_code == 404


def test_get_metrics():
    r = client.get("/api/metrics")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_list_presets():
    r = client.get("/api/presets")
    assert r.status_code == 200
    assert "resource_abundance" in r.json()["presets"]
