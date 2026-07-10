"""
db.py — Database connection helper and all query functions.

This is the ONLY file in the application that issues SQL.
Every other module imports and calls these functions.
"""

import sqlite3
import os

# Path to the SQLite file, resolved relative to this file's directory.
# Override by setting the DATABASE_PATH environment variable.
_DEFAULT_DB = os.path.join(os.path.dirname(__file__), "banking.db")


def get_db_path() -> str:
    return os.environ.get("DATABASE_PATH", _DEFAULT_DB)


def _connect(db_path: str | None = None) -> sqlite3.Connection:
    """Open a connection that returns rows as dicts and enforces FK constraints."""
    conn = sqlite3.connect(db_path or get_db_path())
    conn.row_factory = sqlite3.Row          # rows behave like dicts
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------

def init_db(db_path: str | None = None) -> None:
    """Create tables if they do not already exist. Safe to call on every startup."""
    with _connect(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS customers (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT    NOT NULL UNIQUE,
                password TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS accounts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL REFERENCES customers(id),
                balance     REAL    NOT NULL DEFAULT 0.0
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL REFERENCES accounts(id),
                tx_type    TEXT    NOT NULL CHECK(tx_type IN ('deposit', 'withdrawal')),
                amount     REAL    NOT NULL,
                created_at TEXT    NOT NULL DEFAULT (datetime('now'))
            );
        """)


# ---------------------------------------------------------------------------
# Customer queries
# ---------------------------------------------------------------------------

def get_customer_by_username(username: str, db_path: str | None = None) -> dict | None:
    """Return the customer row for *username*, or None if not found."""
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM customers WHERE username = ?", (username,)
        ).fetchone()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Account queries
# ---------------------------------------------------------------------------

def get_account_by_customer_id(customer_id: int, db_path: str | None = None) -> dict | None:
    """Return the account row for *customer_id*, or None if not found."""
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM accounts WHERE customer_id = ?", (customer_id,)
        ).fetchone()
    return dict(row) if row else None


def update_balance(account_id: int, new_balance: float, db_path: str | None = None) -> None:
    """Overwrite the balance for *account_id*."""
    with _connect(db_path) as conn:
        conn.execute(
            "UPDATE accounts SET balance = ? WHERE id = ?",
            (new_balance, account_id),
        )


# ---------------------------------------------------------------------------
# Transaction queries
# ---------------------------------------------------------------------------

def record_transaction(
    account_id: int,
    tx_type: str,
    amount: float,
    db_path: str | None = None,
) -> None:
    """Insert one row into the transactions log."""
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO transactions (account_id, tx_type, amount) VALUES (?, ?, ?)",
            (account_id, tx_type, amount),
        )
