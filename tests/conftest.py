"""
conftest.py — Shared pytest fixtures for the banking application test suite.

Uses a temporary file-based SQLite database (not :memory:) so that all
connections within a test share the same on-disk state.  Each test gets a
completely fresh database via the autouse reset_db fixture.
"""

import os
import sys
import tempfile
import pytest
from werkzeug.security import generate_password_hash

# ---------------------------------------------------------------------------
# Put BACKEND/ on sys.path before importing anything from the app
# ---------------------------------------------------------------------------
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "BACKEND")
BACKEND_DIR = os.path.abspath(BACKEND_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TEST_USERNAME = "testuser"
TEST_PASSWORD = "password123"
STARTING_BALANCE = 1000.00


# ---------------------------------------------------------------------------
# App fixture (one per session — we recreate the DB per test via reset_db)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def db_path(tmp_path_factory):
    """Return the path to a temporary SQLite file used by all tests."""
    tmp = tmp_path_factory.mktemp("data")
    return str(tmp / "test_banking.db")


@pytest.fixture(scope="session")
def app(db_path):
    """Create a Flask application configured for testing."""
    # Tell db.py which database to use before the app is created
    os.environ["DATABASE_PATH"] = db_path

    from app import create_app
    flask_app = create_app(
        test_config={
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE_PATH": db_path,
        }
    )
    yield flask_app


@pytest.fixture()
def client(app):
    """Return a fresh test client for each test."""
    return app.test_client()


# ---------------------------------------------------------------------------
# Database reset — runs before every individual test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_db(app):
    """
    Drop and recreate all tables, then seed one test customer.
    autouse=True ensures every test starts from a clean, predictable state.
    """
    from db import init_db, _connect

    db_path = app.config["DATABASE_PATH"]

    # Wipe all existing data
    with _connect(db_path) as conn:
        conn.executescript("""
            DROP TABLE IF EXISTS transactions;
            DROP TABLE IF EXISTS accounts;
            DROP TABLE IF EXISTS customers;
        """)

    # Recreate tables
    init_db(db_path)

    # Insert fresh test customer + account
    hashed = generate_password_hash(TEST_PASSWORD)
    with _connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO customers (username, password) VALUES (?, ?)",
            (TEST_USERNAME, hashed),
        )
        customer_id = cur.lastrowid
        conn.execute(
            "INSERT INTO accounts (customer_id, balance) VALUES (?, ?)",
            (customer_id, STARTING_BALANCE),
        )

    yield
