"""
dashboard.py — Dashboard route.

Shows the logged-in customer's name and current account balance.
"""

from flask import Blueprint, render_template, session, redirect, url_for, flash
from db import get_account_by_customer_id
from auth import login_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    customer_id = session["customer_id"]
    customer_name = session.get("customer_name", "Customer")

    account = get_account_by_customer_id(customer_id)
    if account is None:
        # Session refers to a customer with no account — force logout
        session.clear()
        flash("Account not found. Please contact support.", "danger")
        return redirect(url_for("auth.login"))

    return render_template(
        "dashboard.html",
        customer_name=customer_name,
        balance=account["balance"],
    )
