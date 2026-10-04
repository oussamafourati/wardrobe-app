import pytest
from sqlalchemy import text

FULL = {
    "height_cm": 172,
    "top_size": "m",
    "bottom_size": "40",
    "shoe_size": 40.5,
    "hair_color": "brown",
    "eye_color": "green",
    "glasses": True,
}


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def me(client):
    created = client.post("/v1/sessions").json()
    return {"headers": bearer(created["token"]), "user_id": created["user_id"]}


def grant(db_connection, user_id, granted=True):
    db_connection.execute(
        text(
            "INSERT INTO consents (user_id, purpose, granted, policy_version) "
            "VALUES (:uid, 'profile_sensitive', :granted, '2026-09')"
        ),
        {"uid": user_id, "granted": granted},
    )


def put(client, me, payload):
    return client.put("/v1/profile", json=payload, headers=me["headers"])


def test_new_profile_is_empty(client, me):
    body = client.get("/v1/profile", headers=me["headers"]).json()
    assert body["height_cm"] is None
    assert body["undertone"] is None
    assert body["sources"] == {}


def test_put_then_get_roundtrip(client, me):
    assert put(client, me, FULL).status_code == 200
    body = client.get("/v1/profile", headers=me["headers"]).json()
    for field, value in FULL.items():
        assert body[field] == value
        assert body["sources"][field] == "entered"


def test_partial_update_keeps_other_fields(client, me):
    put(client, me, {"height_cm": 172})
    body = put(client, me, {"glasses": False}).json()
    assert body["height_cm"] == 172
    assert body["glasses"] is False


def test_null_clears_field_and_its_source(client, me):
    put(client, me, {"height_cm": 172})
    body = put(client, me, {"height_cm": None}).json()
    assert body["height_cm"] is None
    assert "height_cm" not in body["sources"]


@pytest.mark.parametrize(
    "payload",
    [
        {"height_cm": 50},
        {"height_cm": 251},
        {"shoe_size": 40.3},
        {"shoe_size": 29},
        {"top_size": "banana"},
        {"hair_color": "purple"},
        {"eye_color": "pink"},
        {"undertone": "banana"},
    ],
)
def test_invalid_values_are_rejected(client, me, payload):
    assert put(client, me, payload).status_code == 422


def test_unknown_field_is_rejected(client, me):
    assert put(client, me, {"nonsense": 1}).status_code == 422


def test_sensitive_field_needs_consent(client, db_connection, me):
    denied = put(client, me, {"undertone": "warm"})
    assert denied.status_code == 403
    assert denied.json()["detail"]["code"] == "consent_required"
    grant(db_connection, me["user_id"])
    allowed = put(client, me, {"undertone": "warm"})
    assert allowed.status_code == 200
    assert allowed.json()["undertone"] == "warm"


def test_withdrawn_consent_blocks_again(client, db_connection, me):
    grant(db_connection, me["user_id"], True)
    grant(db_connection, me["user_id"], False)
    assert put(client, me, {"undertone": "cool"}).status_code == 403


def test_clients_cannot_claim_inferred(client, me):
    payload = {"height_cm": 172, "sources": {"height_cm": "inferred"}}
    assert put(client, me, payload).status_code == 422


def test_quiz_source_is_recorded(client, db_connection, me):
    grant(db_connection, me["user_id"])
    body = put(client, me, {"undertone": "olive", "sources": {"undertone": "quiz"}}).json()
    assert body["sources"]["undertone"] == "quiz"


def test_profile_requires_a_token(client):
    assert client.get("/v1/profile").status_code == 401
    assert client.put("/v1/profile", json={"height_cm": 172}).status_code == 401


def test_profiles_are_private_per_user(client):
    first = client.post("/v1/sessions").json()
    second = client.post("/v1/sessions").json()
    client.put("/v1/profile", json={"height_cm": 180}, headers=bearer(first["token"]))
    other = client.get("/v1/profile", headers=bearer(second["token"])).json()
    assert other["height_cm"] is None
