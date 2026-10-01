from sqlalchemy import text

from auth import hash_token


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_create_session_returns_token_and_user(client):
    response = client.post("/v1/sessions", json={"locale": "en-GB"})
    assert response.status_code == 201
    body = response.json()
    assert body["locale"] == "en-GB"
    assert len(body["token"]) >= 40
    assert body["user_id"]


def test_body_is_optional_and_defaults_to_french(client):
    response = client.post("/v1/sessions")
    assert response.status_code == 201
    assert response.json()["locale"] == "fr-FR"


def test_unknown_locale_is_rejected(client):
    assert client.post("/v1/sessions", json={"locale": "xx-XX"}).status_code == 422


def test_me_returns_the_same_identity(client):
    created = client.post("/v1/sessions").json()
    response = client.get("/v1/me", headers=bearer(created["token"]))
    assert response.status_code == 200
    assert response.json()["user_id"] == created["user_id"]


def test_me_requires_a_valid_token(client):
    assert client.get("/v1/me").status_code == 401
    assert client.get("/v1/me", headers=bearer("nope")).status_code == 401
    assert client.get("/v1/me", headers={"Authorization": "Basic abc"}).status_code == 401


def test_only_the_token_hash_is_stored(client, db_connection):
    created = client.post("/v1/sessions").json()
    rows = (
        db_connection.execute(
            text("SELECT token_hash FROM sessions WHERE user_id = :uid"),
            {"uid": created["user_id"]},
        )
        .scalars()
        .all()
    )
    assert rows == [hash_token(created["token"])]
    assert created["token"] not in rows
