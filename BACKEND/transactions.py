"""
transactions.py — Deposit and withdrawal routes.

Both operations follow the same pattern:
  GET  → render the form
  POST → validate input → check business rules → update DB → redirect to dashboard
"""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from db import get_account_by_customer_id, update_balance, record_transaction
from auth import login_required

transactions_bp = Blueprint("transactions", __name__)


# ---------------------------------------------------------------------------
# Deposit
# ---------------------------------------------------------------------------

@transactions_bp.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    if request.method == "POST":
        raw = request.form.get("amount", "").strip()

        # Parse amount
        try:
            amount = float(raw)
        except ValueError:
            flash("Please enter a valid numeric amount.", "danger")
            return render_template("deposit.html"), 400

        # Must be positive
        if amount <= 0:
            flash("Deposit amount must be greater than zero.", "danger")
            return render_template("deposit.html"), 400

        # Fetch account fresh from DB
        customer_id = session["customer_id"]
        account = get_account_by_customer_id(customer_id)
        if account is None:
            flash("Account not found.", "danger")
            return redirect(url_for("auth.login"))

        new_balance = account["balance"] + amount
        update_balance(account["id"], new_balance)
        record_transaction(account["id"], "deposit", amount)

        flash(f"Successfully deposited ${amount:,.2f}. New balance: ${new_balance:,.2f}", "success")
        return redirect(url_for("dashboard.dashboard"))

    return render_template("deposit.html")


# ---------------------------------------------------------------------------
# Withdrawal
# ---------------------------------------------------------------------------

@transactions_bp.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw():
    if request.method == "POST":
        raw = request.form.get("amount", "").strip()

        # Parse amount
        try:
            amount = float(raw)
        except ValueError:
            flash("Please enter a valid numeric amount.", "danger")
            return render_template("withdraw.html"), 400

        # Must be positive
        if amount <= 0:
            flash("Withdrawal amount must be greater than zero.", "danger")
            return render_template("withdraw.html"), 400

        # Fetch account fresh from DB
        customer_id = session["customer_id"]
        account = get_account_by_customer_id(customer_id)
        if account is None:
            flash("Account not found.", "danger")
            return redirect(url_for("auth.login"))

        # Insufficient funds check
        if amount > account["balance"]:
            flash(
                f"Insufficient funds. Your current balance is ${account['balance']:,.2f}.",
                "danger",
            )
            return render_template("withdraw.html"), 400

        new_balance = account["balance"] - amount
        update_balance(account["id"], new_balance)
        record_transaction(account["id"], "withdrawal", amount)

        flash(f"Successfully withdrew ${amount:,.2f}. New balance: ${new_balance:,.2f}", "success")
        return redirect(url_for("dashboard.dashboard"))

    return render_template("withdraw.html")
