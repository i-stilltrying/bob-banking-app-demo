"""
auth.py — Login, logout routes and the login_required session guard.

Blueprint prefix: none (routes are /login and /logout at the root).
"""

import functools
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from werkzeug.security import check_password_hash
from db import get_customer_by_username

auth_bp = Blueprint("auth", __name__)


# ---------------------------------------------------------------------------
# Session guard decorator
# ---------------------------------------------------------------------------

def login_required(view):
    """Wrap a route so unauthenticated users are redirected to /login."""
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if "customer_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Already logged in — go straight to dashboard
    if "customer_id" in session:
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Server-side presence check (in case HTML5 validation was bypassed)
        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template("login.html"), 400

        customer = get_customer_by_username(username)

        # Generic message — do not reveal whether the username exists
        if customer is None or not check_password_hash(customer["password"], password):
            flash("Invalid username or password.", "danger")
            return render_template("login.html"), 401

        # Credentials valid — establish session
        session.clear()
        session["customer_id"] = customer["id"]
        session["customer_name"] = customer["username"]
        return redirect(url_for("dashboard.dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
