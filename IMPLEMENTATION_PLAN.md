# Banking Web Application — Implementation Plan

> **Status:** Planning  
> **Stack:** HTML + Bootstrap (Frontend) · Python Flask (Backend) · SQLite (Database)  
> **Repository layout convention:** `FRONTEND/` · `BACKEND/` · `docs/`

---

## 1. Solution Overview

### Objective

Build a browser-based banking application that allows registered customers to securely log in, view their account balance, deposit funds, and withdraw funds through a clean, responsive interface.

### Scope

| In Scope | Out of Scope |
|---|---|
| Customer authentication (login / logout) | Admin portal or bank-staff interface |
| Personal dashboard with account summary | Multi-currency support |
| View current account balance | Inter-account transfers |
| Deposit funds | Loan or credit features |
| Withdraw funds (with balance check) | Email / SMS notifications |
| Session management | Third-party payment gateway integration |

### Users

| User Role | Description |
|---|---|
| **Customer** | A registered individual with one bank account; the sole end-user of this application |

### Functional Requirements

| ID | Requirement |
|---|---|
| FR-01 | A customer must be able to log in with a username and password |
| FR-02 | Incorrect credentials must be rejected with a clear error message |
| FR-03 | After login, the customer lands on a personal dashboard |
| FR-04 | The dashboard must display the customer's name and current balance |
| FR-05 | The customer must be able to deposit a positive amount into their account |
| FR-06 | The customer must be able to withdraw an amount up to their current balance |
| FR-07 | The system must reject a withdrawal that would result in a negative balance |
| FR-08 | The customer must be able to log out, ending their session |
| FR-09 | All pages except the login page must be protected — unauthenticated access redirects to login |

### Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-01 | All passwords must be stored hashed — never as plain text |
| NFR-02 | Session tokens must be server-side managed via Flask sessions with a secret key |
| NFR-03 | The UI must be responsive and functional on desktop and mobile browsers |
| NFR-04 | Input validation must occur on both the client side (HTML5) and server side (Flask) |
| NFR-05 | The SQLite database file must not be committed to version control |
| NFR-06 | The application must be runnable locally with a single `flask run` command |

### Assumptions

- Each customer has exactly one account; no multi-account support is needed.
- Seed data (at least one test customer) will be loaded via a setup script, not through a registration flow.
- The application is for demo / workshop purposes and is **not** intended for production deployment.
- Python 3.11 and a modern browser (Chrome, Firefox, Safari) are available in the target environment.
- Bootstrap will be loaded via CDN; no custom CSS build pipeline is required.

---

## 2. High-Level Architecture

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    BROWSER (Client)                      │
│                                                          │
│   ┌──────────────────────────────────────────────────┐  │
│   │            FRONTEND  (FRONTEND/)                  │  │
│   │  HTML templates rendered by Jinja2               │  │
│   │  Bootstrap 5 for layout + responsive design      │  │
│   │  Minimal JavaScript for UX enhancements          │  │
│   └────────────────┬─────────────────────────────────┘  │
└────────────────────│────────────────────────────────────┘
                     │  HTTP Request (GET / POST)
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  BACKEND  (BACKEND/)                     │
│                                                          │
│   ┌──────────────────────────────────────────────────┐  │
│   │              Flask Application                    │  │
│   │  Route handlers (blueprints)                     │  │
│   │  Session & authentication middleware             │  │
│   │  Business logic (balance validation, etc.)       │  │
│   └────────────────┬─────────────────────────────────┘  │
└────────────────────│────────────────────────────────────┘
                     │  SQL queries via Python sqlite3 / ORM
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  DATABASE  (BACKEND/)                    │
│                                                          │
│   SQLite file — single-file, zero-config                 │
│   Tables: customers, accounts, transactions              │
└─────────────────────────────────────────────────────────┘
```

### Frontend → Backend → Database Interaction

```
Browser
  │
  │  1. User submits form (login / deposit / withdrawal)
  ▼
Flask Route Handler
  │
  │  2. Validate session cookie → redirect to login if invalid
  │  3. Validate & sanitise form input
  │  4. Call service/helper function (business logic)
  ▼
Database Layer
  │
  │  5. Read or write SQLite via parameterised queries
  │  6. Return result set or row count
  ▼
Flask Route Handler
  │
  │  7. Translate DB result into response context
  ▼
Jinja2 Template
  │
  │  8. Render HTML with dynamic data injected
  ▼
Browser
     9. Display updated UI to customer
```

### Request Lifecycle (Login Example)

```
GET /login
  → Render login.html (no session required)

POST /login
  → Read username + password from form
  → Look up customer by username in DB
  → Verify hashed password
  → On success: create Flask session, redirect to /dashboard
  → On failure: re-render login.html with error message

GET /dashboard  (session required)
  → Read customer_id from session
  → Fetch account balance from DB
  → Render dashboard.html with name + balance
```

---

## 3. Component Design

### Frontend Responsibilities (`FRONTEND/`)

| Responsibility | Detail |
|---|---|
| **Page rendering** | Jinja2 HTML templates served by Flask for each route |
| **Layout & styling** | Bootstrap 5 grid, cards, buttons, and form components |
| **Form presentation** | Login form, deposit form, withdrawal form |
| **Feedback display** | Flash messages for success / error states |
| **Navigation** | Top-bar navbar with account name and logout link |
| **Client-side validation** | HTML5 `required`, `min`, `type="number"` attributes |

The frontend has **no independent server** — templates are rendered and served by Flask. There is no build step, bundler, or API call from the browser; all data is injected server-side.

### Backend Responsibilities (`BACKEND/`)

| Responsibility | Detail |
|---|---|
| **Request routing** | Flask routes mapped to URL paths and HTTP methods |
| **Authentication** | Password hashing with `werkzeug.security`; session management |
| **Session guard** | Decorator or check on every protected route |
| **Business logic** | Balance validation (sufficient funds for withdrawal) |
| **Data access** | Parameterised queries to SQLite; results mapped to Python dicts |
| **Template rendering** | `render_template()` with context variables |
| **Flash messaging** | `flash()` for one-time success / error feedback |
| **App configuration** | Secret key, database path loaded from config or `.env` |

### Database Responsibilities

| Responsibility | Detail |
|---|---|
| **Customer identity** | Store username and hashed password for authentication |
| **Account data** | Maintain current balance per account |
| **Transaction log** | Record every deposit and withdrawal with amount and timestamp |
| **Data integrity** | Enforce non-negative balances through application-layer validation |

The SQLite file lives inside `BACKEND/` and is excluded from version control via `.gitignore`.

---

## 4. Folder Structure

```
workshop-video-demo/                  ← repository root
│
├── FRONTEND/                         ← All UI assets
│   └── templates/                    ← Jinja2 HTML templates (served by Flask)
│       ├── base.html                 ← Shared layout: navbar, Bootstrap CDN, flash messages
│       ├── login.html                ← Login page (username + password form)
│       ├── dashboard.html            ← Post-login landing: name, balance, action buttons
│       ├── deposit.html              ← Deposit form
│       └── withdraw.html             ← Withdrawal form
│
├── BACKEND/                          ← All server-side code + database
│   ├── app.py                        ← Flask application factory / entry point
│   ├── auth.py                       ← Login, logout routes + session helpers
│   ├── dashboard.py                  ← Dashboard route
│   ├── transactions.py               ← Deposit + withdrawal routes + business logic
│   ├── db.py                         ← Database connection helper + query functions
│   ├── seed.py                       ← One-time script to populate test customer data
│   ├── requirements.txt              ← Python dependencies (flask, werkzeug, pytest)
│   └── banking.db                    ← SQLite database file (git-ignored)
│
├── tests/                            ← Pytest test suite (required by CI pipeline)
│   ├── test_auth.py                  ← Tests for login / logout behaviour
│   └── test_transactions.py          ← Tests for deposit / withdrawal logic
│
├── docs/
│   └── demo-setup/                   ← CI and MCP setup guides (existing)
│
├── .gitignore                        ← Excludes banking.db, __pycache__, .env
└── IMPLEMENTATION_PLAN.md            ← This file
```

### Folder Responsibility Summary

| Folder | Responsibility |
|---|---|
| `FRONTEND/templates/` | All HTML views; no logic, no direct DB access |
| `BACKEND/` | All Python source; the only layer that touches the database |
| `tests/` | Automated verification; must not modify production DB |
| `docs/demo-setup/` | Workshop setup guides; no runtime role |

---

## 5. Module Breakdown

### Authentication Module

**Purpose:** Prove customer identity and establish a trusted session.

| Component | Role |
|---|---|
| `auth.py` (routes) | `GET /login`, `POST /login`, `GET /logout` |
| `login.html` | Renders the login form; shows flash error on bad credentials |
| `db.py` (query) | Fetch customer record by username for credential check |
| Session store | Flask server-side session holds `customer_id` after successful login |

**Key behaviours:**
- Passwords are never stored or compared in plain text.
- A failed login re-renders the form; it does **not** reveal whether the username exists.
- Logout clears the session and redirects to the login page.
- All routes below are wrapped in a session guard that redirects unauthenticated users to `/login`.

---

### Dashboard Module

**Purpose:** Give the customer a personalised landing page and route to actions.

| Component | Role |
|---|---|
| `dashboard.py` (route) | `GET /dashboard` — reads session, queries balance, renders view |
| `dashboard.html` | Displays customer name, current balance, and navigation buttons |

**Key behaviours:**
- Reads `customer_id` from session to fetch only that customer's data.
- Provides navigation links to Deposit, Withdraw, and Logout.
- Balance is displayed in a formatted currency style.

---

### Account Management Module

**Purpose:** Maintain and expose accurate account state.

| Component | Role |
|---|---|
| `db.py` (queries) | `get_balance(customer_id)`, `update_balance(customer_id, new_balance)` |
| `transactions.py` | Uses DB helpers to read and write balances atomically |

**Key behaviours:**
- Balance is the single source of truth stored in the database.
- All reads and writes go through `db.py`; routes do not issue raw SQL.
- Balance is never cached in the session — always read fresh from the DB.

---

### Transactions Module

**Purpose:** Execute deposit and withdrawal operations with business-rule enforcement.

| Component | Role |
|---|---|
| `transactions.py` (routes) | `GET/POST /deposit`, `GET/POST /withdraw` |
| `deposit.html` | Form for entering a positive deposit amount |
| `withdraw.html` | Form for entering a withdrawal amount |
| `db.py` (queries) | `record_transaction(customer_id, type, amount)` |

**Key behaviours — Deposit:**
- Amount must be a positive number greater than zero.
- On success: balance is incremented, transaction recorded, flash success message shown.

**Key behaviours — Withdrawal:**
- Amount must be a positive number greater than zero.
- Amount must not exceed current balance — server enforces this check.
- On success: balance is decremented, transaction recorded, flash success message shown.
- On failure: flash error message; no balance change; user remains on the withdrawal page.

---

## 6. Implementation Roadmap

### Development Phases

```
Phase 1 — Project Scaffolding
  Set up folder structure, Flask app entry point, base template,
  requirements.txt, .gitignore, and SQLite connection helper.
  No features yet; just a running "hello world" Flask app.
  Status: [ ] pending

Phase 2 — Database Layer
  Define db.py with all query functions needed by authentication,
  dashboard, and transaction modules. Create seed.py to load test data.
  Status: [ ] pending

Phase 3 — Authentication
  Implement login/logout routes, session management, and
  the session-guard decorator. Build login.html.
  Status: [ ] pending

Phase 4 — Dashboard
  Implement the dashboard route and dashboard.html template.
  Verify session guard redirects unauthenticated requests.
  Status: [ ] pending

Phase 5 — Transactions
  Implement deposit and withdrawal routes with full business-rule
  validation. Build deposit.html and withdraw.html.
  Status: [ ] pending

Phase 6 — Testing
  Write pytest tests covering login success/failure,
  deposit, withdrawal (including insufficient-funds case), and logout.
  Verify tests pass in the existing CI pipeline (banking-app-ci.yml).
  Status: [ ] pending
```

### Estimated Effort

| Phase | Relative Effort |
|---|---|
| Phase 1 — Scaffolding | Small |
| Phase 2 — Database Layer | Small–Medium |
| Phase 3 — Authentication | Medium |
| Phase 4 — Dashboard | Small |
| Phase 5 — Transactions | Medium |
| Phase 6 — Testing | Medium |

### Dependencies

```
Phase 1 must complete before any other phase (all phases depend on project structure).

Phase 2 (DB Layer) must complete before:
  └─ Phase 3 (Authentication) — needs customer lookup query
  └─ Phase 4 (Dashboard) — needs balance query
  └─ Phase 5 (Transactions) — needs balance read/write queries

Phase 3 (Authentication) must complete before:
  └─ Phase 4 (Dashboard) — session guard must exist
  └─ Phase 5 (Transactions) — session guard must exist

Phase 4 and Phase 5 are independent of each other and can proceed in parallel.

Phase 6 (Testing) depends on all prior phases being functionally complete.
```

---

*This document covers planning and architecture only. It does not include database schema DDL, SQL scripts, API contracts, or step-by-step implementation code.*
