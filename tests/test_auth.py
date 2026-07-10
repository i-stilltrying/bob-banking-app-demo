"""
test_auth.py — Tests for login, logout, and the session guard.
"""

import pytest


# ---------------------------------------------------------------------------
# Login — GET
# ---------------------------------------------------------------------------

def test_login_page_loads(client):
    """GET /login should return 200 and contain the login form."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Customer Login" in response.data or b"Log In" in response.data


# ---------------------------------------------------------------------------
# Login — POST: success
# ---------------------------------------------------------------------------

def test_login_success_redirects_to_dashboard(client):
    """Valid credentials should redirect to /dashboard."""
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "password123"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/dashboard" in response.headers["Location"]


def test_login_success_sets_session(client):
    """After login, customer_id should be in the session."""
    with client.session_transaction() as sess:
        assert "customer_id" not in sess  # pre-condition

    client.post("/login", data={"username": "testuser", "password": "password123"})

    with client.session_transaction() as sess:
        assert "customer_id" in sess


# ---------------------------------------------------------------------------
# Login — POST: failures
# ---------------------------------------------------------------------------

def test_login_wrong_password(client):
    """Wrong password should re-render login with a 401 and a generic error."""
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "wrongpass"},
    )
    assert response.status_code == 401
    assert b"Invalid username or password" in response.data


def test_login_wrong_password_no_session(client):
    """Failed login must not establish a session."""
    client.post("/login", data={"username": "testuser", "password": "wrongpass"})
    with client.session_transaction() as sess:
        assert "customer_id" not in sess


def test_login_unknown_username(client):
    """Unknown username should produce the same generic error as wrong password."""
    response = client.post(
        "/login",
        data={"username": "nobody", "password": "anything"},
    )
    assert response.status_code == 401
    assert b"Invalid username or password" in response.data


def test_login_empty_fields(client):
    """Empty username or password should be rejected by the server too."""
    response = client.post("/login", data={"username": "", "password": ""})
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

def test_logout_clears_session(client):
    """Logout should clear the session and redirect to /login."""
    # Log in first
    client.post("/login", data={"username": "testuser", "password": "password123"})

    with client.session_transaction() as sess:
        assert "customer_id" in sess  # confirm logged in

    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    with client.session_transaction() as sess:
        assert "customer_id" not in sess


# ---------------------------------------------------------------------------
# Session guard
# ---------------------------------------------------------------------------

def test_dashboard_requires_login(client):
    """Unauthenticated GET /dashboard should redirect to /login."""
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_deposit_requires_login(client):
    """Unauthenticated GET /deposit should redirect to /login."""
    response = client.get("/deposit", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_withdraw_requires_login(client):
    """Unauthenticated GET /withdraw should redirect to /login."""
    response = client.get("/withdraw", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


# ---------------------------------------------------------------------------
# Already logged in — skip login form
# ---------------------------------------------------------------------------

def test_login_page_redirects_when_already_authenticated(client):
    """A logged-in user visiting /login should be redirected to /dashboard."""
    client.post("/login", data={"username": "testuser", "password": "password123"})
    response = client.get("/login", follow_redirects=False)
    assert response.status_code == 302
    assert "/dashboard" in response.headers["Location"]
