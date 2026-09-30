import pytest
from sqlalchemy import text

from db import engine


@pytest.fixture(scope="session", autouse=True)
def pgvector_extension():
    """Make sure pgvector exists. In Sprint 1 this moves into a migration."""
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
