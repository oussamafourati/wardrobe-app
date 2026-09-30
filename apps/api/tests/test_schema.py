import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from db import engine


@pytest.fixture
def conn():
    """A connection whose changes are always rolled back, so tests leave no data behind."""
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            yield connection
        finally:
            transaction.rollback()


def new_user(conn):
    return conn.execute(text("INSERT INTO users DEFAULT VALUES RETURNING id")).scalar_one()


def count(conn, table, uid):
    return conn.execute(
        text(f"SELECT count(*) FROM {table} WHERE user_id = :uid"), {"uid": uid}
    ).scalar_one()


def test_deleting_a_user_erases_profile_and_consents(conn):
    uid = new_user(conn)
    conn.execute(
        text("INSERT INTO profiles (user_id, height_cm, glasses) VALUES (:uid, 170, true)"),
        {"uid": uid},
    )
    for granted in (True, False):
        conn.execute(
            text(
                "INSERT INTO consents (user_id, purpose, granted, policy_version) "
                "VALUES (:uid, 'analytics', :granted, '2026-09')"
            ),
            {"uid": uid, "granted": granted},
        )
    stored = conn.execute(
        text("SELECT glasses FROM profiles WHERE user_id = :uid"), {"uid": uid}
    ).scalar_one()
    assert stored is True
    assert count(conn, "consents", uid) == 2

    conn.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": uid})

    assert count(conn, "profiles", uid) == 0
    assert count(conn, "consents", uid) == 0


def test_profile_rejects_out_of_range_height(conn):
    uid = new_user(conn)
    with pytest.raises(IntegrityError):
        with conn.begin_nested():
            conn.execute(
                text("INSERT INTO profiles (user_id, height_cm) VALUES (:uid, 50)"),
                {"uid": uid},
            )


def test_consent_rejects_unknown_purpose(conn):
    uid = new_user(conn)
    with pytest.raises(IntegrityError):
        with conn.begin_nested():
            conn.execute(
                text(
                    "INSERT INTO consents (user_id, purpose, granted, policy_version) "
                    "VALUES (:uid, 'nonsense', true, '2026-09')"
                ),
                {"uid": uid},
            )
