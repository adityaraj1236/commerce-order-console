# Commerce Order Console

An internal order management console for a store operations team that takes orders over the
phone. It replaces a spreadsheet with one place to create orders, find them, move them through
fulfilment and keep inventory accurate.

- **Backend:** FastAPI, SQLAlchemy 2.0, PostgreSQL. See [backend/README.md](backend/README.md).
- **Frontend:** Next.js (App Router), TypeScript, TanStack Query. See [frontend/README.md](frontend/README.md).

No login, payments or cloud deployment are part of the scope.

---

## Contents

1. [Features](#features)
2. [Technology stack](#technology-stack)
3. [Architecture](#architecture)
4. [Repository structure](#repository-structure)
5. [Prerequisites](#prerequisites)
6. [Quick start](#quick-start)
7. [Environment configuration](#environment-configuration)
8. [Database, migrations and seed data](#database-migrations-and-seed-data)
9. [Running the application](#running-the-application)
10. [Tests and quality checks](#tests-and-quality-checks)
11. [API documentation](#api-documentation)
12. [Walkthrough](#walkthrough)
13. [How data consistency is guaranteed](#how-data-consistency-is-guaranteed)

---

## Features

**Create orders**

- Product catalogue with prices, available stock and a stock level (in stock, low stock, out of stock).
- Cart with multiple products, quantity controls, line totals and an order total.
- Products that are out of stock cannot be added; quantities cannot exceed available stock.
- A warning bar appears when a cart line holds all remaining stock of a product.
- The server calculates every price and total and rejects the whole order if any line is unavailable.

**Find orders**

- Order list with partial, case-insensitive search by order reference, a status filter and pagination.
- Filters are kept in the URL, so they survive opening an order and coming back.
- Order detail with every item, unit price, quantity, line total, grand total and status.

**Manage fulfilment**

- `PLACED → PACKED → SHIPPED`, and cancellation from `PLACED` or `PACKED` only.
- The detail page shows only the actions the server allows next; the server rejects any other transition.
- Cancelling asks for confirmation and returns the items to stock exactly once.

**Dashboard**

- Order counts by status, total products, low-stock and out-of-stock counts.
- Each card links to the matching filtered view.

**Data consistency**

- Stock deduction and order creation commit together or not at all.
- Row-level locks prevent overselling when two orders compete for the last units.
- Orders and stock are stored in PostgreSQL and survive restarts.

---

## Technology stack

| Layer    | Technology                                                                                                               |
| -------- | ------------------------------------------------------------------------------------------------------------------------ |
| Frontend | Next.js 15 (App Router), React 19, TypeScript (strict), Tailwind CSS v4 (design tokens), TanStack Query v5, Lucide icons |
| Backend  | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 (sync), Alembic                                                        |
| Database | PostgreSQL 16 (Docker), psycopg 3                                                                                        |
| Testing  | pytest, HTTPX / FastAPI TestClient, a dedicated PostgreSQL test database                                                 |
| Tooling  | uv, Ruff, ESLint, Prettier, Docker Compose                                                                               |

---

## Architecture

```
┌──────────────────────────┐   JSON over HTTP    ┌──────────────────────────┐   SQL    ┌────────────┐
│ Frontend (Next.js)       │ ──────────────────► │ Backend (FastAPI)        │ ───────► │ PostgreSQL │
│                          │     /api/v1/...     │                          │          │            │
│ pages → hooks (TanStack) │ ◄────────────────── │ router → service → crud  │ ◄─────── │ products   │
│      → lib/api client    │  {"error": {...}}   │   transactions + locks   │          │ orders     │
└──────────────────────────┘    on failure       └──────────────────────────┘          │ order_items│
                                                                                        └────────────┘
```

- The **backend** is organised by feature (`products`, `orders`, `dashboard`). Each feature has a
  router (HTTP), a service (business rules and transactions) and a `crud` module (queries).
- The **frontend** never calculates real prices or decides business rules. Stock levels and the
  next allowed order statuses come from the API.
- Every error from the API has the same shape:
  `{"error": {"code": "...", "message": "...", "details": [...] | null}}`.

---

## Repository structure

```
order-management-system/
├── backend/                 FastAPI application, migrations, seed script, tests
│   ├── app/                 core/, db/, products/, orders/, dashboard/, health/, main.py
│   ├── migrations/          Alembic environment and versions
│   ├── scripts/             seed.py, seed_data.py
│   └── tests/               unit/ and integration/
├── frontend/                Next.js application
│   └── src/                 app/, components/, page_components/, hooks/, lib/api/, types/, utils/
├── docker/postgres/init/    creates the test database on first start
├── docker-compose.yml       local PostgreSQL
└── README.md
```

---

## Prerequisites

| Tool                             | Version              | Used for                         |
| -------------------------------- | -------------------- | -------------------------------- |
| Docker Desktop                   | recent               | PostgreSQL                       |
| Python                           | 3.12+                | backend                          |
| [uv](https://docs.astral.sh/uv/) | 0.5+                 | Python dependencies and commands |
| Node.js                          | 20+ (22 recommended) | frontend                         |
| npm                              | 10+                  | frontend dependencies            |

---

## Quick start

From the repository root:

```bash
# 1. Start PostgreSQL (dev database + test database)
docker compose up -d

# 2. Backend: install, migrate, seed, run
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run python -m scripts.seed
uv run fastapi dev app/main.py          # http://localhost:8000

# 3. Frontend (in a second terminal)
cd frontend
cp .env.example .env.local
npm install
npm run dev                             # http://localhost:3000
```

On Windows PowerShell use `Copy-Item .env.example .env` instead of `cp`.

Open <http://localhost:3000>. The console opens on the dashboard.

---

## Environment configuration

Real `.env` files are ignored by Git. Copy the examples and adjust if needed.

**`backend/.env`** (from `backend/.env.example`)

| Variable              | Default                                                                  | Description                                                                                 |
| --------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| `DATABASE_URL`        | `postgresql+psycopg://postgres:password@localhost:5434/commerce_console` | Development database                                                                        |
| `ENVIRONMENT`         | `development`                                                            | `development` gives readable logs plus log files; any other value gives JSON logs on stdout |
| `LOW_STOCK_THRESHOLD` | `5`                                                                      | Products with 1 to this many units count as low stock                                       |

Tests use `TEST_DATABASE_URL`, which defaults to
`postgresql+psycopg://postgres:password@localhost:5434/commerce_console_test`.

**`frontend/.env.local`** (from `frontend/.env.example`)

| Variable              | Default                        | Description                 |
| --------------------- | ------------------------------ | --------------------------- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | Base URL of the backend API |

---

## Database, migrations and seed data

**Database.** `docker compose up -d` starts PostgreSQL 16 in a container named
`commerce-console-postgres`. Data is stored in the `postgres_data` Docker volume, so it survives
container restarts and `docker compose down`. On the first start the script in
`docker/postgres/init/` also creates the separate `commerce_console_test` database.

> The container is published on host port **5434** so it does not clash with a locally installed
> PostgreSQL on 5432/5433. Change `POSTGRES_HOST_PORT` and the URLs above if you need another port.

> If the volume already existed before the init script was added, create the test database once
> by hand: `docker exec commerce-console-postgres psql -U postgres -c "CREATE DATABASE commerce_console_test;"`

**Migrations** (from `backend/`):

```bash
uv run alembic upgrade head            # apply all migrations
uv run alembic downgrade base          # remove all tables
uv run alembic revision --autogenerate -m "describe change"   # after changing a model
uv run alembic check                   # confirms models and database match
```

**Seed data** (from `backend/`):

```bash
uv run python -m scripts.seed
```

Inserts 58 synthetic products (several out of stock, several low on stock). The script is
idempotent: products whose SKU already exists are skipped, so running it again never duplicates
rows or resets stock changed by real orders.

To start from a clean database:

```bash
docker compose down -v && docker compose up -d
cd backend && uv run alembic upgrade head && uv run python -m scripts.seed
```

---

## Running the application

| Service    | Command (from its folder)                | URL                     |
| ---------- | ---------------------------------------- | ----------------------- |
| PostgreSQL | `docker compose up -d` (repository root) | `localhost:5434`        |
| Backend    | `uv run fastapi dev app/main.py`         | <http://localhost:8000> |
| Frontend   | `npm run dev`                            | <http://localhost:3000> |

Production-style frontend build: `npm run build && npm run start`.

---

## Tests and quality checks

**Backend** (from `backend/`, PostgreSQL must be running):

```bash
uv run pytest                 # all 120 tests
uv run pytest tests/unit      # fast, no database
uv run pytest -k concurrent   # only the concurrency tests
uv run ruff check .           # lint
uv run ruff format --check .  # formatting
```

Tests run against `commerce_console_test` only and refuse to start if the database name does not
end in `_test`. Each test starts from empty tables.

Coverage includes the brief's required cases and acceptance examples:

- successful single- and multi-product orders, totals and stock deduction;
- insufficient stock rejecting the whole order with no stock change and no order row;
- every invalid status transition rejected with the order and stock unchanged;
- cancellation restoring stock exactly once, including five simultaneous cancellations;
- five simultaneous orders for the last unit, with exactly one succeeding;
- orders and stock surviving a real restart of the API process.

**Frontend** (from `frontend/`):

```bash
npm run check   # ESLint + design-token check + TypeScript + Prettier
```

---

## API documentation

With the backend running:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- OpenAPI JSON: <http://localhost:8000/openapi.json>

The endpoint reference, request and response shapes and error codes are in
[backend/README.md](backend/README.md#api-reference).

---

## Walkthrough

A short tour that covers every requirement, using the seeded catalogue.

1. **Dashboard** (<http://localhost:3000>). Order counts by status and stock counts. Click
   **Packed** to open the order list filtered to orders ready to ship.
2. **Products.** All products with price, available units and a stock badge. The
   Noise-Cancelling Headset is out of stock.
3. **Create Order.** Search the catalogue, add a keyboard twice and a mouse once. The cart shows
   line totals and a total of ₹10,897.00. The headset's button reads _Unavailable_.
   Add a low-stock product until the _Stock limit reached_ bar appears.
4. **Place the order.** A success message shows the new reference (for example
   `ORD-20261126-JJE5JA`) and the catalogue shows the reduced stock.
5. **Insufficient stock.** Put the last units of a product in the cart, set that product's stock
   to 0 in the database, then place the order. The order is rejected, the message names the
   product, nothing is created and no stock changes.
6. **Orders.** Search by part of the reference, filter by status, open an order.
7. **Fulfilment.** On a placed order, click _Mark as packed_, then _Mark as shipped_. A shipped
   order offers no further actions.
8. **Cancellation.** On another placed order, click _Cancel order_ and confirm. Its items go back
   to stock. Sending the cancellation again (for example from a second browser tab or Swagger)
   returns `409 order_already_cancelled` and stock does not change.
9. **Restart.** Stop and start the backend and `docker compose`; the orders and stock are unchanged.

---

## How data consistency is guaranteed

| Risk                               | Protection                                                                                                                |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Partial orders                     | Stock check, deduction and order insert run in one transaction (`with session.begin()`); any error rolls everything back. |
| Overselling under concurrency      | `SELECT ... FOR UPDATE` locks the product rows in id order; a second order waits, then sees the reduced stock.            |
| Stock restored twice               | `SELECT ... FOR UPDATE` on the order row; a second cancellation waits, then sees `CANCELLED` and is rejected.             |
| Deadlocks                          | Orders and cancellations always lock product rows in the same (id) order.                                                 |
| Negative stock or prices           | Database `CHECK` constraints (`stock_quantity >= 0`, `price > 0`, `quantity > 0`).                                        |
| Trusting client prices             | The order request accepts only product ids and quantities; extra fields such as `unit_price` are rejected with 422.       |
| Price changes affecting old orders | Each order line stores a snapshot of the product name and unit price.                                                     |
| Floating-point money errors        | `NUMERIC(12,2)` in the database, `Decimal` in Python, exact strings in JSON, integer paise in the browser.                |

Both concurrency tests were checked by removing the lock: without it, they fail (five orders for
one unit all succeed; five cancellations all restore stock).
