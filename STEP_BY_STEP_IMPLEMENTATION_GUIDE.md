# Banking Web Application — Step-by-Step Implementation Guide

> **Reference:** [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md)  
> **Stack:** HTML + Bootstrap 5 (Frontend) · Python Flask (Backend) · SQLite (Database)  
> **Approach:** Plain-English instructions describing *what to build and why* — not copy-paste code.

---

## Table of Contents

1. [Environment Setup](#1-environment-setup)
2. [Backend Implementation](#2-backend-implementation)
3. [Frontend Implementation](#3-frontend-implementation)
4. [Integration Steps](#4-integration-steps)
5. [Validation Rules](#5-validation-rules)
6. [Testing](#6-testing)
7. [Deployment](#7-deployment)

---

## 1. Environment Setup

### 1.1 Prerequisites Check

Before writing a single line of code, confirm the following tools are installed on the machine:

- **Python 3.11 or higher** — the runtime for Flask. Check by running the version command in your terminal. If it is missing, download it from python.org.
- **pip** — Python's package manager. It ships with Python 3.11 automatically.
- **A terminal / shell** — macOS Terminal, Linux bash, or Windows PowerShell all work.
- **A code editor** — VS Code is recommended but any editor will do.
- **A modern browser** — Chrome, Firefox, or Safari for manual testing.

---

### 1.2 Create the Project Folder Structure

Create the top-level directories that will house every part of the application. The structure must match what the plan defines exactly, because Flask needs to know where to find templates and the CI pipeline expects a `tests/` folder at the root:

```
workshop-video-demo/
├── FRONTEND/
│   └── templates/
├── BACKEND/
├── tests/
└── docs/           ← already exists, leave it alone
```

Create each empty folder manually or via your terminal. Do **not** put any files inside them yet — that comes in later steps.

---

### 1.3 Create a Virtual Environment

A virtual environment isolates this project's Python packages from everything else on your machine. This prevents version conflicts and ensures the CI pipeline gets a clean install.

- Navigate your terminal into the `BACKEND/` folder.
- Create a virtual environment there, giving it a name like `venv`.
- Activate it. On macOS/Linux the activation command differs from Windows — check the Python docs for your OS.
- Once activated, your terminal prompt will show the environment name. Every `pip install` from this point forward installs into this isolated environment only.

> **Convention:** Never commit the `venv/` folder to git. Add it to `.gitignore` immediately.

---

### 1.4 Create `requirements.txt`

Inside `BACKEND/`, create a plain-text file called `requirements.txt`. List each package on its own line. The packages this project needs are:

- `flask` — the web framework.
- `werkzeug` — ships with Flask but list it explicitly; you will use its password-hashing utilities.
- `pytest` — the testing framework the CI pipeline expects.
- `pytest-flask` — a plugin that makes testing Flask apps easier (provides a test client fixture).

Pin the major version of each package (e.g., `flask>=3.0`) to prevent unexpected upgrades from breaking the app.

Install everything at once by telling pip to read from `requirements.txt`. This single command is what the CI pipeline runs too, so your local environment will match CI exactly.

---

### 1.5 Flask Setup Verification

Before building any features, verify Flask runs on the machine:

- Inside `BACKEND/`, create a temporary `app.py` with the absolute minimum Flask application — just enough to return "Hello" at the root URL.
- Tell Flask where to find the application. Flask looks for an environment variable called `FLASK_APP` that points to the file. Set this in your terminal session or in a `.env` file (but never commit `.env` to git).
- Run `flask run` from the `BACKEND/` directory. Flask will print the local URL (typically `http://127.0.0.1:5000`).
- Open that URL in a browser. If you see your greeting, the environment is working correctly.
- Delete the temporary greeting content — the real application structure starts in Section 2.

---

### 1.6 Configure `.gitignore`

At the repository root, create or update `.gitignore` to exclude files that must never be committed:

- The SQLite database file (`banking.db`) — contains real customer data.
- The virtual environment folder (`venv/`).
- Python cache folders (`__pycache__/`, `*.pyc`).
- The `.env` file — contains the Flask secret key.
- macOS system files (`.DS_Store`).

Doing this now avoids accidentally committing sensitive files later.

---

## 2. Backend Implementation

### 2.1 Database Module — `BACKEND/db.py`

> **Build this first.** Every other backend module depends on it.

`db.py` is the **single place** that touches the SQLite database. No other file should write raw SQL. This keeps database logic in one place and makes it easy to test.

**Connection helper logic:**
- Write a function that opens a connection to `banking.db` using Python's built-in `sqlite3` module.
- Set the connection to return rows as dictionaries (not tuples) — this makes accessing columns by name much easier in routes (e.g., `row['balance']` instead of `row[0]`).
- Tell SQLite to enforce foreign key constraints by running a pragma command right after connecting.
- The database file path should come from a config variable, not be hard-coded as a string.

**Table creation logic:**
- Write a function that creates the three tables if they do not already exist: `customers`, `accounts`, and `transactions`.
- Use `CREATE TABLE IF NOT EXISTS` so this function is safe to call every time the app starts.
- The `customers` table stores an ID, a username (unique), and the hashed password.
- The `accounts` table stores an ID, the customer ID (foreign key), and the current balance.
- The `transactions` table stores an ID, the account ID, a type field (either `"deposit"` or `"withdrawal"`), the amount, and a timestamp.

**Query functions to write:**
Each function takes the minimum arguments needed and returns a result. Keep them narrow and focused:

| Function name | What it does |
|---|---|
| `get_customer_by_username(username)` | Returns the full customer row matching a username, or `None` if not found. Used during login. |
| `get_account_by_customer_id(customer_id)` | Returns the account row for a given customer. Used on dashboard, deposit, and withdraw. |
| `update_balance(account_id, new_balance)` | Overwrites the balance field for the given account. Called after every successful transaction. |
| `record_transaction(account_id, tx_type, amount)` | Inserts one row into the transactions table. Always called alongside `update_balance`. |

> **Rule:** Always use parameterised queries (placeholders like `?` in sqlite3). Never build SQL strings by concatenating user input — that creates SQL injection vulnerabilities.

---

### 2.2 Database Seed Script — `BACKEND/seed.py`

This is a one-time script that sets up test data so you can actually log in during development. It is not part of the Flask app itself.

**What the script should do:**

1. Call the table-creation function from `db.py` to ensure the tables exist.
2. Check whether the test customer already exists before inserting — this makes the script safe to run multiple times without creating duplicates.
3. Insert one test customer with a known username (e.g., `testuser`) and a password that has been **hashed** using `werkzeug.security.generate_password_hash`. Never insert a plain-text password.
4. Insert one account row linked to that customer with a starting balance (e.g., 1000.00).
5. Print a confirmation message when done.

Run this script once from the `BACKEND/` directory before starting the app. After running it, `banking.db` will exist and contain one usable account.

---

### 2.3 Flask Application Entry Point — `BACKEND/app.py`

`app.py` is where Flask is instantiated and configured. Think of it as the wiring diagram that connects all the other modules together.

**What `app.py` should do:**

1. Create the Flask application instance.
2. Tell Flask where the templates folder is. Since templates live in `FRONTEND/templates/` rather than the default `templates/` folder, you must provide the path explicitly when creating the app instance.
3. Set the `SECRET_KEY` configuration value. This is required for sessions to work. Load it from an environment variable rather than hard-coding it. If no environment variable is set, use a fallback default for development only.
4. Call the `init_db()` function from `db.py` so tables are created on every startup (safe because of `IF NOT EXISTS`).
5. Register all the route modules (blueprints). Import and attach `auth`, `dashboard`, and `transactions` blueprints.
6. Add a root route (`/`) that immediately redirects to `/login` so users always land somewhere useful.

---

### 2.4 Authentication Routes — `BACKEND/auth.py`

This module handles everything related to proving identity: logging in and logging out.

**Organise it as a Flask Blueprint** with the prefix `/auth` or no prefix — both work. Using a Blueprint keeps auth routes in one file and makes it easy to register them in `app.py`.

**`GET /login` — Show the login form:**
- This route requires no session check — it is the only public page in the app.
- Simply render `login.html`. Pass no data context; the form is static.
- If the user is already logged in (session already has `customer_id`), redirect them straight to the dashboard — they do not need to log in again.

**`POST /login` — Process the login form:**
- Read the `username` and `password` fields from the submitted form.
- Call `get_customer_by_username(username)` from `db.py`.
- If no customer is found, flash a generic error message like "Invalid username or password" and re-render the login page. Do **not** say "username not found" — that reveals information.
- If a customer is found, call `werkzeug.security.check_password_hash`, passing the stored hash and the submitted password. This function returns `True` if they match, `False` if not.
- If the password is wrong, flash the same generic error and re-render the login page.
- If everything checks out: store the `customer_id` (and optionally the customer name for display) in `flask.session`, then redirect to `/dashboard`.

**`GET /logout` — End the session:**
- Call `session.clear()` to remove all session data.
- Flash a brief confirmation message like "You have been logged out."
- Redirect to `/login`.

---

### 2.5 Session Guard — The Login-Required Decorator

Before building the dashboard or transaction routes, create a reusable session guard. This is a Python decorator (a function that wraps another function) that protects every route that requires the user to be logged in.

**How it works:**
- The decorator checks whether `customer_id` exists in `flask.session`.
- If it does, the wrapped route function runs normally.
- If it does not, the decorator flashes a message like "Please log in to continue" and redirects to `/login`.

Place this decorator in `auth.py` or a shared `utils.py` file. Import and apply it to every route in `dashboard.py` and `transactions.py`. This one decorator handles FR-09 (unauthenticated access protection) for the entire application.

---

### 2.6 Dashboard Route — `BACKEND/dashboard.py`

This module has exactly one job: show the customer their account information.

**Organise it as a Flask Blueprint.**

**`GET /dashboard`:**
- Apply the session guard decorator.
- Read `customer_id` from `flask.session`.
- Call `get_account_by_customer_id(customer_id)` from `db.py` to get the current balance. Do not read balance from the session — always read it fresh from the database.
- Also retrieve the customer's name from the database (or from the session if you stored it at login) so you can greet them by name.
- Render `dashboard.html`, passing the customer name and balance as context variables.

---

### 2.7 Transaction Routes — `BACKEND/transactions.py`

This module handles both deposit and withdrawal. Both follow the same pattern — read form input, validate it, apply the change, record it — so they are naturally grouped together.

**Organise it as a Flask Blueprint.**

**`GET /deposit` — Show the deposit form:**
- Apply the session guard decorator.
- Render `deposit.html`. No data context needed; the form is static.

**`POST /deposit` — Process a deposit:**
- Apply the session guard decorator.
- Read the `amount` field from the form. Immediately try to convert it to a float. If conversion fails (user typed letters), flash an error and re-render the deposit form.
- If the amount is zero or negative, flash an error and re-render. Positive amounts only.
- Get the customer's current account from the database using `get_account_by_customer_id`.
- Calculate the new balance: `current_balance + amount`.
- Call `update_balance(account_id, new_balance)` to save the new balance.
- Call `record_transaction(account_id, "deposit", amount)` to log the operation.
- Flash a success message confirming the deposit amount.
- Redirect to `/dashboard`. After a successful POST, always redirect — this prevents the form from being re-submitted if the user hits the browser's back/refresh button.

**`GET /withdraw` — Show the withdrawal form:**
- Apply the session guard decorator.
- Render `withdraw.html`. No data context needed.

**`POST /withdraw` — Process a withdrawal:**
- Apply the session guard decorator.
- Read and convert the `amount` field, exactly as in the deposit flow.
- If the amount is zero or negative, flash an error and re-render.
- Get the customer's current account from the database.
- **Business rule check:** If `amount > current_balance`, flash an error message like "Insufficient funds" and re-render the withdrawal form. Do not touch the balance.
- If the amount is valid: calculate the new balance (`current_balance - amount`), call `update_balance`, and call `record_transaction` with type `"withdrawal"`.
- Flash a success message and redirect to `/dashboard`.

---

### 2.8 Error Handling

Flask's default error pages are plain and unhelpful in a styled application. Register custom error handlers in `app.py`:

- **404 Not Found** — shown when a user navigates to a URL that does not exist. Render a simple `404.html` template with a "Page not found" message and a link back to the dashboard.
- **500 Internal Server Error** — shown when the server encounters an unexpected exception. Render a `500.html` template with a generic "Something went wrong" message. Never expose raw stack traces to users.

Register these handlers on the Flask app object using `@app.errorhandler(404)` and `@app.errorhandler(500)`.

---

## 3. Frontend Implementation

> The frontend has no independent server. All templates are Jinja2 files rendered and served by Flask. Bootstrap is loaded via CDN — no build step, no bundler.

### 3.1 Base Layout — `FRONTEND/templates/base.html`

Build `base.html` first. Every other template will extend it. This ensures a consistent look across all pages without repeating the same HTML.

**What `base.html` must contain:**

- The full HTML5 document structure (`<!DOCTYPE html>`, `<head>`, `<body>`).
- A `<meta name="viewport">` tag for responsive behaviour on mobile.
- A `<link>` tag in `<head>` pointing to the Bootstrap 5 CDN stylesheet URL.
- A `<script>` tag before `</body>` pointing to the Bootstrap 5 CDN JavaScript bundle (needed for navbar collapse on mobile).
- A **navigation bar** at the top of the page. The navbar should show the application name on the left. If the user is logged in, show their name and a Logout button on the right. If not logged in, show nothing (or just the app name). Use Jinja2's `session` object to check login state.
- A **flash message block** below the navbar. Use Jinja2 to loop over `get_flashed_messages(with_categories=True)`. Render each message as a Bootstrap alert (`alert-success` for success, `alert-danger` for errors). Add a close button so users can dismiss messages.
- A **main content block** — a Jinja2 `{% block content %}{% endblock %}` placeholder in the page's `<main>` element. Child templates will inject their unique content here.

---

### 3.2 Login Page — `FRONTEND/templates/login.html`

This is the only page accessible without a session. It must be clean and focused — one job only.

**Layout guidance:**
- Extend `base.html`.
- Centre the login card on the page using Bootstrap's grid (`col-md-4 offset-md-4`) or utility classes (`d-flex justify-content-center`).
- Use a Bootstrap `card` component. The card header should say something like "Welcome Back" or the application name.
- Inside the card body, place a single `<form>` with `method="POST"` and `action="/login"`.
- Two input fields: one for username (`type="text"`, `name="username"`, `required`), one for password (`type="password"`, `name="password"`, `required`).
- A full-width Bootstrap primary button labelled "Log In".
- Do not include any registration link — there is no registration flow.

**Behaviour reminder:** Flash messages are already handled in `base.html`, so a failed login error will appear automatically above the card without any extra template work.

---

### 3.3 Dashboard Page — `FRONTEND/templates/dashboard.html`

This is the home page after login. It communicates account state and provides navigation to actions.

**Layout guidance:**
- Extend `base.html`.
- Use a Bootstrap container with a greeting heading: "Hello, [customer name]" — use the `{{ customer_name }}` variable passed from the route.
- Below the greeting, place a Bootstrap `card` styled with a distinct background (e.g., `bg-primary text-white`) to display the balance prominently. Show it as a currency value: "Current Balance: $1,000.00". Use Jinja2's `{{ "%.2f"|format(balance) }}` filter to format the number.
- Below the balance card, place two Bootstrap buttons side by side: "Deposit Funds" (links to `/deposit`) and "Withdraw Funds" (links to `/withdraw`). Use the Bootstrap grid to space them evenly.
- The Logout link is in the navbar (from `base.html`) — no need to duplicate it here.

---

### 3.4 Deposit Form — `FRONTEND/templates/deposit.html`

A focused, single-input form for depositing money.

**Layout guidance:**
- Extend `base.html`.
- Centre a Bootstrap card with a header labelled "Deposit Funds".
- Inside, a `<form>` with `method="POST"` and `action="/deposit"`.
- One input field: label "Amount", `type="number"`, `name="amount"`, `min="0.01"`, `step="0.01"`, `required`. The `min` and `step` attributes enforce positive decimals at the browser level.
- A Bootstrap success-styled ("btn-success") button labelled "Deposit".
- A secondary link or button labelled "Back to Dashboard" that navigates to `/dashboard`.

---

### 3.5 Withdrawal Form — `FRONTEND/templates/withdraw.html`

Structurally identical to the deposit form but with different labels and destination.

**Layout guidance:**
- Extend `base.html`.
- Centre a Bootstrap card with a header labelled "Withdraw Funds".
- Inside, a `<form>` with `method="POST"` and `action="/withdraw"`.
- One input field: label "Amount", `type="number"`, `name="amount"`, `min="0.01"`, `step="0.01"`, `required`.
- A Bootstrap warning-styled ("btn-warning") button labelled "Withdraw" to visually distinguish it from the deposit action.
- A "Back to Dashboard" link.

> **Note:** Client-side validation (`min="0.01"`) stops obvious mistakes, but the server always validates too. If a user bypasses the browser form (e.g., via Postman), the server-side check in `transactions.py` is the real safety net.

---

### 3.6 Bootstrap Layout Conventions

Apply these consistently across all templates:

| Convention | Reason |
|---|---|
| Wrap all page content in `<div class="container mt-4">` | Centres content and adds top margin below the navbar |
| Use `mb-3` on form groups | Consistent vertical spacing between fields |
| Use `form-control` class on all inputs | Bootstrap styling for form fields |
| Use `form-label` class on all labels | Correct label styling |
| Use `d-grid` on form buttons | Makes buttons full-width inside their container |
| Add `autocomplete="off"` to amount fields | Prevents browsers from suggesting previous transaction amounts |

---

## 4. Integration Steps

### 4.1 Connect Flask to SQLite

The Flask app and the SQLite database are connected through `db.py`. Here is the sequence that ties everything together:

1. When `app.py` starts, it calls `init_db()`. This opens a connection to `banking.db` (creating the file if it does not exist) and creates the three tables.
2. When any route needs data, it imports and calls the relevant function from `db.py` (e.g., `get_account_by_customer_id`). The function opens a fresh connection, runs the query, closes the connection, and returns the result.
3. The route takes the result (a Python dict) and passes it to `render_template()` as keyword arguments.

**Important connection pattern:** In this application, each database call opens and closes its own connection. This is safe for SQLite and removes the need for connection-pooling logic. The `with` statement (context manager) ensures the connection is always closed, even if an error occurs.

---

### 4.2 Connect Frontend Templates to Flask Routes

Templates and routes are connected through two mechanisms:

**Route → Template (rendering):**
Every route ends with either `return render_template('page.html', variable=value)` or `return redirect(url_for('blueprint.route_function'))`. Flask finds the template file by looking in the folder specified when the app was created — which, in this project, is `FRONTEND/templates/`.

**Template → Route (form submission):**
Every HTML `<form>` has an `action` attribute pointing to a Flask route URL (e.g., `action="/deposit"`) and a `method` of `POST`. When the user clicks Submit, the browser sends a POST request to that URL. Flask matches it to the correct route function.

**Template links:**
Navigation links use the Flask `url_for()` function inside Jinja2 expressions (e.g., `href="{{ url_for('auth.logout') }}"`). This is better than hard-coding `/auth/logout` because if you ever change a URL, all links update automatically.

**Telling Flask where templates live:**
When creating the Flask app instance in `app.py`, pass the `template_folder` argument pointing to `../FRONTEND/templates` (relative to `BACKEND/`). Without this, Flask defaults to looking for a `templates/` folder inside the same directory as `app.py`.

---

### 4.3 Blueprint Registration Order

Register blueprints in `app.py` in this order:

1. `auth` blueprint — must be first because it defines the `/login` and `/logout` routes that the session guard redirects to.
2. `dashboard` blueprint.
3. `transactions` blueprint.

All three blueprints import from `db.py`. Make sure `db.py` does not import from any blueprint — this avoids circular imports.

---

## 5. Validation Rules

### 5.1 Login Validation

| Check | Layer | Response on failure |
|---|---|---|
| Username field is not empty | Client (HTML5 `required`) | Browser blocks form submission |
| Password field is not empty | Client (HTML5 `required`) | Browser blocks form submission |
| Username exists in database | Server (`db.py` query) | Flash generic error; re-render login |
| Password matches stored hash | Server (`werkzeug.check_password_hash`) | Flash generic error; re-render login |

**Key principle:** Both checks (username not found AND wrong password) produce the **exact same error message** to the user. This prevents an attacker from using the login form to discover which usernames exist in the system.

---

### 5.2 Balance Validation (on every transaction)

Before processing any deposit or withdrawal, the server must:

1. Read the customer's current balance from the database — never rely on a value the user submitted or a value cached from a previous request.
2. Confirm the account exists. If `get_account_by_customer_id` returns `None`, the session is corrupt — log out the user and redirect to login.

---

### 5.3 Deposit Checks

| Check | Layer | Response on failure |
|---|---|---|
| Amount field is not empty | Client (HTML5 `required`) | Browser blocks submission |
| Amount is a positive number (> 0) | Client (`min="0.01"`) | Browser blocks submission |
| Amount can be parsed as a float | Server (try/except on conversion) | Flash error; re-render deposit form |
| Amount is greater than zero (after conversion) | Server (conditional check) | Flash error; re-render deposit form |

After all checks pass, compute `new_balance = current_balance + amount` and save it.

---

### 5.4 Withdrawal Checks

| Check | Layer | Response on failure |
|---|---|---|
| Amount field is not empty | Client (HTML5 `required`) | Browser blocks submission |
| Amount is a positive number (> 0) | Client (`min="0.01"`) | Browser blocks submission |
| Amount can be parsed as a float | Server (try/except on conversion) | Flash error; re-render withdrawal form |
| Amount is greater than zero (after conversion) | Server (conditional check) | Flash error; re-render withdrawal form |
| Amount does not exceed current balance | Server (compare amount vs. DB balance) | Flash "Insufficient funds"; re-render; **no balance change** |

After all checks pass, compute `new_balance = current_balance - amount` and save it.

**Critical rule:** The insufficient-funds check must happen **after** reading the balance fresh from the database on that exact request. Never compare against a balance read in a previous request.

---

### 5.5 Session Validation

On every protected route (dashboard, deposit, withdraw):

| Check | What happens |
|---|---|
| `customer_id` present in session | Route proceeds normally |
| `customer_id` absent from session | Flash "Please log in"; redirect to `/login` |

The session guard decorator handles this automatically. No individual route needs to repeat the check.

---

## 6. Testing

### 6.1 Test Setup

The CI pipeline (`docs/demo-setup/banking-app-ci.yml`) runs `pytest` on the `tests/` directory. Tests must work against an **in-memory SQLite database**, not `banking.db`. This prevents tests from corrupting development data and makes tests fast and independent.

**How to set up the test environment:**

- In your test files, create a pytest `fixture` that builds a fresh Flask app configured to use an in-memory SQLite connection (`:memory:`).
- Another fixture should use `pytest-flask`'s `client` fixture — this gives you a test HTTP client that can send GET and POST requests to your routes without running a real server.
- A third fixture should call `init_db()` and insert a known test customer with a known password before each test, so every test starts from a clean, predictable state.

---

### 6.2 Unit Tests — `tests/test_auth.py`

These tests verify the authentication logic in isolation.

**Test: successful login**
- POST to `/login` with the correct username and password.
- Assert the response redirects to `/dashboard` (HTTP 302).
- Assert that `customer_id` is now in the session.

**Test: wrong password**
- POST to `/login` with correct username but wrong password.
- Assert the response is HTTP 200 (re-renders login, not a redirect).
- Assert the response body contains the error message text.
- Assert `customer_id` is NOT in the session.

**Test: unknown username**
- POST to `/login` with a username that does not exist.
- Assert same outcomes as wrong password — same message, no session.

**Test: logout clears session**
- Log in first, then GET `/logout`.
- Assert the response redirects to `/login`.
- Assert `customer_id` is no longer in the session.

**Test: dashboard redirects unauthenticated users**
- Without logging in, GET `/dashboard`.
- Assert the response redirects to `/login` (the session guard is working).

---

### 6.3 Unit Tests — `tests/test_transactions.py`

These tests verify deposit and withdrawal business logic.

**Test: successful deposit**
- Log in with the test client. GET `/deposit` — assert HTTP 200.
- POST `/deposit` with a valid positive amount.
- Assert redirect to `/dashboard`.
- Query the test database directly and assert the balance increased by the deposited amount.
- Query the transactions table and assert one row was recorded with the correct type and amount.

**Test: deposit with zero amount**
- Log in, POST `/deposit` with `amount=0`.
- Assert HTTP 200 (re-renders form, not a redirect).
- Assert an error message appears in the response body.
- Assert balance has not changed.

**Test: deposit with negative amount**
- Same pattern as zero amount. Assert rejection and no balance change.

**Test: successful withdrawal**
- Log in, POST `/withdraw` with an amount less than the starting balance.
- Assert redirect to `/dashboard`.
- Assert balance decreased correctly.
- Assert one transaction row was recorded.

**Test: withdrawal exceeds balance (insufficient funds)**
- Log in with a customer whose balance is, say, 100.00.
- POST `/withdraw` with `amount=500.00`.
- Assert HTTP 200 (re-renders form).
- Assert "Insufficient funds" (or similar) appears in the response body.
- Assert balance has NOT changed in the database.

**Test: withdrawal of exact balance (edge case)**
- POST `/withdraw` with an amount exactly equal to the current balance.
- Assert this succeeds — zero balance is acceptable, negative balance is not.

---

### 6.4 Manual Testing Checklist

Run through this checklist in a real browser before considering the application complete:

**Authentication flow:**
- [ ] Navigate to `http://127.0.0.1:5000` — confirm it redirects to `/login`
- [ ] Submit the login form with empty fields — confirm the browser prevents submission
- [ ] Submit with wrong password — confirm the error message appears and the form is shown again
- [ ] Submit with correct credentials — confirm you land on the dashboard and see your name and balance
- [ ] Copy the dashboard URL and open it in a new incognito/private window — confirm you are redirected to login

**Dashboard:**
- [ ] Confirm the balance is formatted as a currency (e.g., $1,000.00)
- [ ] Confirm your customer name is displayed
- [ ] Confirm the Deposit and Withdraw buttons are visible and clickable
- [ ] Confirm the Logout button/link appears in the navbar

**Deposit flow:**
- [ ] Click Deposit — confirm the deposit form loads
- [ ] Submit with no amount — confirm browser prevents it
- [ ] Submit with a negative number — confirm browser prevents it (or server rejects it)
- [ ] Submit a valid amount — confirm you are redirected to the dashboard
- [ ] Confirm the balance on the dashboard has increased by the deposited amount

**Withdrawal flow:**
- [ ] Click Withdraw — confirm the withdrawal form loads
- [ ] Submit an amount greater than the balance — confirm "Insufficient funds" message appears and balance is unchanged
- [ ] Submit a valid amount — confirm redirect to dashboard
- [ ] Confirm the balance has decreased by the withdrawn amount
- [ ] Try to withdraw the exact remaining balance — confirm it succeeds and balance shows 0.00

**Logout:**
- [ ] Click Logout — confirm you are redirected to login
- [ ] Press the browser Back button — confirm you are NOT taken back to the dashboard (session is cleared)

**Responsive design:**
- [ ] Resize the browser to a narrow width (or use browser DevTools mobile view) — confirm the navbar collapses and the layout does not break

---

## 7. Deployment

### 7.1 Run Locally

Running locally requires three commands after the initial setup is complete:

**Step 1 — Activate the virtual environment**
Navigate to `BACKEND/` and activate `venv`. Your terminal prompt will show the environment name when activated.

**Step 2 — Seed the database (first time only)**
Run `seed.py` directly with Python. This creates `banking.db` and inserts the test customer. You only need to do this once. If you delete `banking.db` and start fresh, run it again.

**Step 3 — Start Flask**
Set the `FLASK_APP` environment variable to `app.py` and the `FLASK_ENV` variable to `development`. Development mode enables the auto-reloader (so Flask restarts when you save a file) and the debugger (so errors show detail in the browser).

Then run `flask run`. The terminal will print the address. Open it in a browser.

**To stop the server:** Press `Ctrl+C` in the terminal.

---

### 7.2 Running Tests Locally

From the repository root (not `BACKEND/`), run `pytest tests/`. Pytest discovers and runs all files matching `test_*.py` in the `tests/` folder.

To see verbose output (individual test names and pass/fail), run `pytest tests/ -v`.

Ensure all tests pass before pushing. The CI pipeline runs the exact same command.

---

### 7.3 CI Pipeline Integration

The existing [`docs/demo-setup/banking-app-ci.yml`](docs/demo-setup/banking-app-ci.yml) is already configured for this project. It will:

1. Check out the code on a fresh Ubuntu machine.
2. Set up Python 3.11.
3. Install packages from `BACKEND/requirements.txt`.
4. Run `pytest tests/` if the `tests/` directory exists.

No changes to the CI file are needed. The pipeline will trigger automatically on any push to `main` or `feature/**` branches.

---

### 7.4 Production Considerations

This application is built for workshop / demo purposes. If it were ever moved toward production, the following changes would be required:

| Area | Development approach | What production would need |
|---|---|---|
| **Secret key** | Fallback default string | Randomly generated, rotated secret stored in a secrets manager |
| **Database** | SQLite file | PostgreSQL or MySQL for concurrency and reliability |
| **Server** | Flask's built-in development server | A production WSGI server such as Gunicorn or uWSGI |
| **HTTPS** | HTTP only | TLS certificate and redirect from HTTP to HTTPS (via nginx or a load balancer) |
| **Debug mode** | `FLASK_ENV=development` | Must be disabled — never expose stack traces in production |
| **Password policy** | Any string accepted | Minimum length, complexity rules, account lockout after failed attempts |
| **Session security** | Default Flask cookie | `SESSION_COOKIE_SECURE=True`, `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE='Lax'` |
| **CSRF protection** | No protection | Flask-WTF with CSRF tokens on every form |
| **Logging** | No structured logging | Application-level logging for audit trails of all transactions |

These are not part of this implementation but should be understood before any production deployment.

---

*This guide covers step-by-step implementation instructions in plain English. For architecture decisions and module responsibilities, refer to [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md).*
