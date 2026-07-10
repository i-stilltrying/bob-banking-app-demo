"""
app.py — Flask application factory and entry point.

Usage (from BACKEND/ with venv active):
    flask run
or:
    python app.py
"""

import os
import sys

from flask import Flask, redirect, url_for, render_template

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app(test_config: dict | None = None) -> Flask:
    """
    Create and configure the Flask application.

    test_config: dict of config overrides used by the pytest fixture
                 (e.g. to point at an in-memory database).
    """
    # Templates live in FRONTEND/templates/, one level above BACKEND/
    template_dir = os.path.join(os.path.dirname(__file__), "..", "FRONTEND", "templates")
    template_dir = os.path.abspath(template_dir)

    app = Flask(__name__, template_folder=template_dir)

    # -----------------------------------------------------------------------
    # Configuration
    # -----------------------------------------------------------------------
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    app.config["DATABASE_PATH"] = os.environ.get(
        "DATABASE_PATH",
        os.path.join(os.path.dirname(__file__), "banking.db"),
    )

    if test_config:
        app.config.update(test_config)

    # Propagate DATABASE_PATH into the environment so db.py can read it
    os.environ["DATABASE_PATH"] = app.config["DATABASE_PATH"]

    # -----------------------------------------------------------------------
    # Initialise database tables on startup
    # -----------------------------------------------------------------------
    from db import init_db
    init_db(app.config["DATABASE_PATH"])

    # -----------------------------------------------------------------------
    # Register blueprints
    # -----------------------------------------------------------------------
    from auth import auth_bp
    from dashboard import dashboard_bp
    from transactions import transactions_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp)

    # -----------------------------------------------------------------------
    # Root redirect
    # -----------------------------------------------------------------------
    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    # -----------------------------------------------------------------------
    # Custom error handlers
    # -----------------------------------------------------------------------
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("500.html"), 500

    return app


# ---------------------------------------------------------------------------
# Entry point for `python app.py`
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Add BACKEND/ to sys.path so sibling modules are importable
    sys.path.insert(0, os.path.dirname(__file__))
    application = create_app()
    application.run(debug=True)
