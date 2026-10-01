import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import main
from db import engine, get_db


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    """Bring the database to the latest schema before any test runs."""
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def db_connection():
    """A connection inside a transaction that is always rolled back."""
    connection = engine.connect()
    outer = connection.begin()
    try:
        yield connection
    finally:
        outer.rollback()
        connection.close()


@pytest.fixture
def client(db_connection):
    """A test client whose database writes are rolled back after each test."""

    def override_get_db():
        with Session(bind=db_connection, join_transaction_mode="create_savepoint") as session:
            yield session

    main.app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(main.app)
    finally:
        main.app.dependency_overrides.clear()
