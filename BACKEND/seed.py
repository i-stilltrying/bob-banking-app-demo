"""
seed.py — One-time script to populate the database with a test customer.

Run once from the BACKEND/ directory:
    python seed.py

Safe to re-run: checks for the existing username before inserting.
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash
from db import init_db, get_db_path, _connect

TEST_USERNAME = "testuser"
TEST_PASSWORD = "password123"
STARTING_BALANCE = 1000.00


def seed() -> None:
    db_path = get_db_path()
    print(f"Database: {db_path}")

    # Ensure tables exist
    init_db(db_path)

    with _connect(db_path) as conn:
        # Check if the test customer already exists
        existing = conn.execute(
            "SELECT id FROM customers WHERE username = ?", (TEST_USERNAME,)
        ).fetchone()

        if existing:
            print(f"Customer '{TEST_USERNAME}' already exists — skipping insert.")
            return

        # Insert customer with hashed password
        hashed = generate_password_hash(TEST_PASSWORD)
        cursor = conn.execute(
            "INSERT INTO customers (username, password) VALUES (?, ?)",
            (TEST_USERNAME, hashed),
        )
        customer_id = cursor.lastrowid

        # Insert linked account with starting balance
        conn.execute(
            "INSERT INTO accounts (customer_id, balance) VALUES (?, ?)",
            (customer_id, STARTING_BALANCE),
        )

    print(f"Seeded customer '{TEST_USERNAME}' with balance ${STARTING_BALANCE:.2f}")
    print(f"Login with  username='{TEST_USERNAME}'  password='{TEST_PASSWORD}'")


if __name__ == "__main__":
    seed()
