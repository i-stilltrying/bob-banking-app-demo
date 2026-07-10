"""
test_transactions.py — Tests for deposit and withdrawal routes.
"""

import pytest
from db import _connect


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def login(client):
    """Log in with the seeded test customer."""
    return client.post(
        "/login",
        data={"username": "testuser", "password": "password123"},
        follow_redirects=True,
    )


def get_balance(app):
    """Read the test customer's balance directly from the DB."""
    db_path = app.config["DATABASE_PATH"]
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT a.balance FROM accounts a "
            "JOIN customers c ON c.id = a.customer_id "
            "WHERE c.username = 'testuser'"
        ).fetchone()
    return row["balance"] if row else None


def get_transaction_count(app):
    """Count rows in the transactions table."""
    db_path = app.config["DATABASE_PATH"]
    with _connect(db_path) as conn:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM transactions").fetchone()
    return row["cnt"]


# ---------------------------------------------------------------------------
# Deposit — GET
# ---------------------------------------------------------------------------

def test_deposit_page_loads(client):
    """GET /deposit (authenticated) should return 200."""
    login(client)
    response = client.get("/deposit")
    assert response.status_code == 200
    assert b"Deposit" in response.data


# ---------------------------------------------------------------------------
# Deposit — POST: success
# ---------------------------------------------------------------------------

def test_deposit_success_redirects_to_dashboard(client, app):
    """A valid deposit should redirect to /dashboard."""
    login(client)
    response = client.post(
        "/deposit",
        data={"amount": "200"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/dashboard" in response.headers["Location"]


def test_deposit_increases_balance(client, app):
    """Depositing 200 should increase balance from 1000 to 1200."""
    login(client)
    client.post("/deposit", data={"amount": "200"})
    assert get_balance(app) == pytest.approx(1200.00)


def test_deposit_records_transaction(client, app):
    """A successful deposit should create one transaction row."""
    login(client)
    before = get_transaction_count(app)
    client.post("/deposit", data={"amount": "50"})
    assert get_transaction_count(app) == before + 1


def test_deposit_decimal_amount(client, app):
    """Fractional deposits should work correctly."""
    login(client)
    client.post("/deposit", data={"amount": "0.50"})
    assert get_balance(app) == pytest.approx(1000.50)


# ---------------------------------------------------------------------------
# Deposit — POST: validation failures
# ---------------------------------------------------------------------------

def test_deposit_zero_amount_rejected(client, app):
    """Depositing zero should be rejected without changing the balance."""
    login(client)
    response = client.post("/deposit", data={"amount": "0"})
    assert response.status_code == 400
    assert get_balance(app) == pytest.approx(1000.00)


def test_deposit_negative_amount_rejected(client, app):
    """Negative deposit should be rejected."""
    login(client)
    response = client.post("/deposit", data={"amount": "-50"})
    assert response.status_code == 400
    assert get_balance(app) == pytest.approx(1000.00)


def test_deposit_non_numeric_rejected(client, app):
    """Non-numeric deposit amount should be rejected."""
    login(client)
    response = client.post("/deposit", data={"amount": "abc"})
    assert response.status_code == 400
    assert get_balance(app) == pytest.approx(1000.00)


def test_deposit_empty_amount_rejected(client, app):
    """Empty deposit amount should be rejected."""
    login(client)
    response = client.post("/deposit", data={"amount": ""})
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Withdrawal — GET
# ---------------------------------------------------------------------------

def test_withdraw_page_loads(client):
    """GET /withdraw (authenticated) should return 200."""
    login(client)
    response = client.get("/withdraw")
    assert response.status_code == 200
    assert b"Withdraw" in response.data


# ---------------------------------------------------------------------------
# Withdrawal — POST: success
# ---------------------------------------------------------------------------

def test_withdraw_success_redirects_to_dashboard(client, app):
    """A valid withdrawal should redirect to /dashboard."""
    login(client)
    response = client.post(
        "/withdraw",
        data={"amount": "100"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/dashboard" in response.headers["Location"]


def test_withdraw_decreases_balance(client, app):
    """Withdrawing 100 should decrease balance from 1000 to 900."""
    login(client)
    client.post("/withdraw", data={"amount": "100"})
    assert get_balance(app) == pytest.approx(900.00)


def test_withdraw_records_transaction(client, app):
    """A successful withdrawal should create one transaction row."""
    login(client)
    before = get_transaction_count(app)
    client.post("/withdraw", data={"amount": "100"})
    assert get_transaction_count(app) == before + 1


def test_withdraw_exact_balance_succeeds(client, app):
    """Withdrawing the entire balance (1000) should succeed, leaving 0.00."""
    login(client)
    response = client.post("/withdraw", data={"amount": "1000"})
    assert get_balance(app) == pytest.approx(0.00)


# ---------------------------------------------------------------------------
# Withdrawal — POST: insufficient funds
# ---------------------------------------------------------------------------

def test_withdraw_exceeds_balance_rejected(client, app):
    """Withdrawal amount greater than balance should be rejected."""
    login(client)
    response = client.post("/withdraw", data={"amount": "5000"})
    assert response.status_code == 400
    assert b"Insufficient funds" in response.data
    # Balance must be unchanged
    assert get_balance(app) == pytest.approx(1000.00)


def test_withdraw_exceeds_balance_no_transaction_recorded(client, app):
    """Failed withdrawal must not create a transaction row."""
    login(client)
    before = get_transaction_count(app)
    client.post("/withdraw", data={"amount": "5000"})
    assert get_transaction_count(app) == before


# ---------------------------------------------------------------------------
# Withdrawal — POST: other validation failures
# ---------------------------------------------------------------------------

def test_withdraw_zero_amount_rejected(client, app):
    login(client)
    response = client.post("/withdraw", data={"amount": "0"})
    assert response.status_code == 400
    assert get_balance(app) == pytest.approx(1000.00)


def test_withdraw_negative_amount_rejected(client, app):
    login(client)
    response = client.post("/withdraw", data={"amount": "-10"})
    assert response.status_code == 400
    assert get_balance(app) == pytest.approx(1000.00)


def test_withdraw_non_numeric_rejected(client, app):
    login(client)
    response = client.post("/withdraw", data={"amount": "xyz"})
    assert response.status_code == 400
    assert get_balance(app) == pytest.approx(1000.00)


# ---------------------------------------------------------------------------
# Sequential operations
# ---------------------------------------------------------------------------

def test_multiple_deposits_accumulate(client, app):
    """Two deposits should add up correctly."""
    login(client)
    client.post("/deposit", data={"amount": "200"})
    client.post("/deposit", data={"amount": "300"})
    assert get_balance(app) == pytest.approx(1500.00)


def test_deposit_then_withdraw(client, app):
    """Deposit then withdraw should result in the correct net balance."""
    login(client)
    client.post("/deposit", data={"amount": "500"})   # 1500
    client.post("/withdraw", data={"amount": "200"})  # 1300
    assert get_balance(app) == pytest.approx(1300.00)
