from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_db():
    response = client.get("/health/db")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["pgvector"] != "not installed"


def test_health_db_hides_error_details(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("password=supersecret host=10.0.0.5")

    monkeypatch.setattr(main.engine, "connect", boom)
    response = client.get("/health/db")
    assert response.status_code == 503
    assert "supersecret" not in response.text
