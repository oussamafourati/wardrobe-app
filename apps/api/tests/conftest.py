import pytest
from alembic import command
from alembic.config import Config


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    """Bring the database to the latest schema before any test runs."""
    command.upgrade(Config("alembic.ini"), "head")
