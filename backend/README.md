# Commerce Order Console: Backend

FastAPI service that owns every business rule of the console: product catalogue, order
creation with transactional stock deduction, order search, fulfilment status transitions,
cancellation with stock restoration, and dashboard counts.

Setup, environment variables and the full run guide are in the [root README](../README.md).

---

## Contents

1. [Quick commands](#quick-commands)
2. [Project layout](#project-layout)
3. [Request flow and layers](#request-flow-and-layers)
4. [Data model](#data-model)
5. [API reference](#api-reference)
6. [Error responses](#error-responses)
7. [Business rules](#business-rules)
8. [Transactions and concurrency](#transactions-and-concurrency)
9. [Module and function reference](#module-and-function-reference)
10. [Logging](#logging)
11. [Testing](#testing)
12. [Adding a new feature](#adding-a-new-feature)

---

## Quick commands

```bash
uv sync                                  # install dependencies
uv run alembic upgrade head              # create / update tables
uv run python -m scripts.seed            # insert sample products (idempotent)
uv run fastapi dev app/main.py           # run with auto-reload on http://localhost:8000
uv run pytest                            # run all tests (needs PostgreSQL)
uv run ruff check . && uv run ruff format --check .
```

---

## Project layout

The code is organised **by feature**. Each feature folder holds everything for that feature.

```
backend/
├── app/
│   ├── main.py                  App factory: logging, middleware, error handlers, routers
│   ├── core/
│   │   ├── config.py            Settings from environment variables / .env
│   │   ├── exceptions.py        Business exceptions mapped to HTTP status codes
│   │   ├── error_handlers.py    Turns every exception into the standard error JSON
│   │   ├── schemas.py           ErrorResponse schema + helper for documenting errors
│   │   ├── logging.py           setup_logging(), log_with_context(), formatters
│   │   └── middleware.py        Request ID + one access log line per request
│   ├── db/
│   │   ├── base.py              Declarative Base with a constraint naming convention
│   │   ├── mixins.py            UUID primary key and created_at / updated_at columns
│   │   ├── session.py           Engine, session factory, DbSession dependency
│   │   └── all_models.py        Imports every model so Alembic can see them
│   ├── health/router.py         GET /health
│   ├── products/
│   │   ├── models.py            Product table
│   │   ├── schemas.py           ProductRead, ProductListResponse
│   │   ├── stock.py             StockLevel + classify_stock()
│   │   ├── crud.py              Product queries, including row locking
│   │   ├── service.py           list / get logic
│   │   └── router.py            /products endpoints
│   ├── orders/
│   │   ├── models.py            Order, OrderItem, OrderStatus
│   │   ├── schemas.py           Request and response models
│   │   ├── status_rules.py      The order state machine (pure logic)
│   │   ├── crud.py              Order queries, search, pagination, row locking
│   │   ├── service.py           create, get, list
│   │   ├── fulfilment_service.py  Status changes and cancellation
│   │   └── router.py            /orders endpoints
│   └── dashboard/               Aggregate counts for the dashboard
├── migrations/                  Alembic env.py and versions/
├── scripts/
│   ├── seed.py                  Inserts the sample catalogue
│   └── seed_data.py             58 synthetic products
└── tests/
    ├── conftest.py              Points the app at the test database (with a safety guard)
    ├── unit/                    No database needed
    └── integration/             Real PostgreSQL, real migrations, real transactions
```

---

## Request flow and layers

```
HTTP request
  → RequestContextMiddleware      assigns X-Request-ID, writes the access log
  → router.py                     validates input (Pydantic), calls the service
  → service.py                    business rules; owns the transaction
  → crud.py                       SQLAlchemy queries; never commits
  → PostgreSQL
  ← schemas.py                    response model (only declared fields leave the API)
  ← error_handlers.py             any exception becomes {"error": {...}}
```

| Layer        | Responsibility                        | Rule                                                                |
| ------------ | ------------------------------------- | ------------------------------------------------------------------- |
| `router.py`  | HTTP only                             | No business logic. Receives `session: DbSession`, returns a schema. |
| `service.py` | Business rules, transactions, logging | Plain functions. Writes run inside `with session.begin():`.         |
| `crud.py`    | Database queries                      | Plain functions. Never commits or rolls back.                       |
| `schemas.py` | Request and response shapes           | Money is `Decimal`, serialised as a string.                         |
| `models.py`  | Tables and constraints                | SQLAlchemy 2.0 typed mappings.                                      |

Transactions are opened in the service, not in a dependency's teardown, so the commit always
happens **before** the response is sent. The API can never report success for a write that did
not commit.

---

## Data model

```
products 1 ──── * order_items * ──── 1 orders
```

**products**

| Column                     | Type          | Constraint                    |
| -------------------------- | ------------- | ----------------------------- |
| `id`                       | UUID          | primary key                   |
| `name`                     | VARCHAR(200)  | not null                      |
| `sku`                      | VARCHAR(64)   | **unique**                    |
| `description`              | TEXT          | not null                      |
| `price`                    | NUMERIC(12,2) | `CHECK (price > 0)`           |
| `stock_quantity`           | INTEGER       | `CHECK (stock_quantity >= 0)` |
| `created_at`, `updated_at` | TIMESTAMPTZ   | default `now()`               |

**orders**

| Column                     | Type                | Constraint                                          |
| -------------------------- | ------------------- | --------------------------------------------------- |
| `id`                       | UUID                | primary key                                         |
| `order_reference`          | VARCHAR(32)         | **unique**, e.g. `ORD-20261126-JJE5JA`              |
| `status`                   | ENUM `order_status` | `PLACED`, `PACKED`, `SHIPPED`, `CANCELLED`; indexed |
| `total_amount`             | NUMERIC(12,2)       | `CHECK (total_amount >= 0)`                         |
| `created_at`, `updated_at` | TIMESTAMPTZ         | `created_at` indexed (list is newest first)         |

**order_items**

| Column         | Type          | Constraint                                                      |
| -------------- | ------------- | --------------------------------------------------------------- |
| `id`           | UUID          | primary key                                                     |
| `order_id`     | UUID          | FK → `orders.id` `ON DELETE CASCADE`, indexed                   |
| `product_id`   | UUID          | FK → `products.id` `ON DELETE RESTRICT`, indexed                |
| `product_name` | VARCHAR(200)  | snapshot at order time                                          |
| `unit_price`   | NUMERIC(12,2) | snapshot at order time, `CHECK (> 0)`                           |
| `quantity`     | INTEGER       | `CHECK (quantity > 0)`                                          |
| `line_total`   | NUMERIC(12,2) | `unit_price × quantity`, `CHECK (> 0)`                          |
|                |               | `UNIQUE (order_id, product_id)`: one line per product per order |

The schema is created only through Alembic (`migrations/versions/`). `uv run alembic check`
confirms the models and the database match.

---

## API reference

Base URL: `http://localhost:8000/api/v1`. Interactive docs: <http://localhost:8000/docs>.

| Method | Path                                  | Purpose                                            | Success | Errors        |
| ------ | ------------------------------------- | -------------------------------------------------- | ------- | ------------- |
| GET    | `/health`                             | Liveness check                                     | 200     |               |
| GET    | `/products`                           | List all products                                  | 200     |               |
| GET    | `/products/{product_id}`              | Get one product                                    | 200     | 404, 422      |
| POST   | `/orders`                             | Place an order                                     | 201     | 404, 409, 422 |
| GET    | `/orders`                             | List orders with search, status filter, pagination | 200     | 422           |
| GET    | `/orders/{order_id}`                  | Get one order with its items                       | 200     | 404, 422      |
| GET    | `/orders/reference/{order_reference}` | Get one order by its reference                     | 200     | 404, 422      |
| PATCH  | `/orders/{order_id}/status`           | Change status; cancelling restores stock           | 200     | 404, 409, 422 |
| GET    | `/dashboard/summary`                  | Counts by order status and stock level             | 200     |               |

Every response carries an `X-Request-ID` header (generated, or reused from a well-formed incoming one).

### GET /products

All products, sorted by name.

```json
{
  "items": [
    {
      "id": "9d80e2f9-6607-41b5-b1cf-c9d5aa49b323",
      "name": "Noise-Cancelling Headset",
      "sku": "HS-NC-005",
      "description": "Over-ear Bluetooth headset with active noise cancellation and boom mic.",
      "price": "7999.00",
      "stock_quantity": 0,
      "created_at": "2026-11-25T12:03:12.178629Z",
      "updated_at": "2026-11-25T12:03:12.178629Z",
      "is_in_stock": false,
      "stock_level": "out_of_stock"
    }
  ],
  "total": 58
}
```

- `price` is an exact decimal string.
- `stock_level` is `in_stock`, `low_stock` (1 to `LOW_STOCK_THRESHOLD` units) or `out_of_stock`.
  The frontend shows this value and never decides the threshold itself.

### GET /products/{product_id}

One product, same shape as an item above. `404` if the id does not exist, `422` if it is not a UUID.

### POST /orders

Request: product ids and quantities only. Prices and totals are never accepted from the client.

```json
{
  "items": [
    { "product_id": "PRODUCT_UUID", "quantity": 2 },
    { "product_id": "PRODUCT_UUID_2", "quantity": 1 }
  ]
}
```

Validation (all `422`):

- `items` must not be empty;
- each product may appear only once;
- `quantity` must be a whole number from 1 to 2,147,483,647 (strict: `"2"`, `2.5` and `true` are rejected);
- unknown fields such as `unit_price` or `total_amount` are rejected.

Response `201`:

```json
{
  "id": "d632d140-58fa-46c4-985c-1c8be2c6ebb4",
  "order_reference": "ORD-20261126-JJE5JA",
  "status": "PLACED",
  "total_amount": "10897.00",
  "created_at": "2026-11-26T04:04:12.031Z",
  "updated_at": "2026-11-26T04:04:12.031Z",
  "items": [
    {
      "product_id": "…",
      "product_name": "Mechanical Keyboard (TKL)",
      "unit_price": "4499.00",
      "quantity": 2,
      "line_total": "8998.00"
    },
    {
      "product_id": "…",
      "product_name": "Wireless Ergonomic Mouse",
      "unit_price": "1899.00",
      "quantity": 1,
      "line_total": "1899.00"
    }
  ],
  "item_count": 3,
  "allowed_transitions": ["PACKED", "CANCELLED"]
}
```

- `item_count` is the total number of units.
- `allowed_transitions` lists the statuses this order may move to next.

Failures:

| Case                                   | Status | `code`               | `details`                                                                                                         |
| -------------------------------------- | ------ | -------------------- | ----------------------------------------------------------------------------------------------------------------- |
| A product does not exist               | 404    | `not_found`          | one entry per missing product, e.g. `items.1.product_id`                                                          |
| Not enough stock for one or more lines | 409    | `insufficient_stock` | one entry per short line, e.g. `{"field": "items.1.quantity", "message": "Product B: requested 1, available 0."}` |

In both cases no order is created and no stock changes.

### GET /orders

Query parameters:

| Name        | Type                                             | Default | Description                                                                                |
| ----------- | ------------------------------------------------ | ------- | ------------------------------------------------------------------------------------------ |
| `reference` | string, max 32                                   |         | Partial, case-insensitive match on the order reference. `%` and `_` are treated literally. |
| `status`    | `PLACED` \| `PACKED` \| `SHIPPED` \| `CANCELLED` |         | Only orders in this status                                                                 |
| `page`      | integer ≥ 1                                      | 1       | Page number                                                                                |
| `page_size` | integer 1–100                                    | 20      | Orders per page                                                                            |

Response (newest first):

```json
{
  "items": [
    {
      "id": "…",
      "order_reference": "ORD-20261125-5CQCKL",
      "status": "PLACED",
      "total_amount": "649.00",
      "item_count": 1,
      "created_at": "…",
      "updated_at": "…"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

`item_count` is computed in SQL, so order items are not loaded for the list.

### GET /orders/{order_id}

The full order, same shape as the `POST /orders` response.

### GET /orders/reference/{order_reference}

The full order by exact reference. Input is trimmed and upper-cased first, so
`ord-20261125-5cqckl` finds `ORD-20261125-5CQCKL`. Partial references return `404`
(use `GET /orders?reference=` to search).

### PATCH /orders/{order_id}/status

```json
{ "status": "PACKED" }
```

Returns the updated order. Allowed transitions:

```
PLACED → PACKED → SHIPPED
PLACED → CANCELLED
PACKED → CANCELLED
```

| Case                                                                       | Status | `code`                      |
| -------------------------------------------------------------------------- | ------ | --------------------------- |
| Skipped or backward transition (`PLACED → SHIPPED`, `SHIPPED → PACKED`, …) | 409    | `invalid_status_transition` |
| Any change from `SHIPPED` or `CANCELLED`                                   | 409    | `invalid_status_transition` |
| Cancelling an already cancelled order                                      | 409    | `order_already_cancelled`   |
| Unknown status value or extra field                                        | 422    | `validation_error`          |
| Unknown order                                                              | 404    | `not_found`                 |

Cancelling restores the stock of every line in the same transaction as the status change.
A rejected request leaves the status and stock unchanged.

### GET /dashboard/summary

```json
{
  "orders": {
    "total": 6,
    "by_status": { "PLACED": 1, "PACKED": 2, "SHIPPED": 1, "CANCELLED": 2 }
  },
  "products": {
    "total": 58,
    "low_stock": 11,
    "out_of_stock": 7,
    "low_stock_threshold": 5
  }
}
```

Every status is always present. Counting happens in PostgreSQL (`GROUP BY`, `COUNT(*) FILTER`).

---

## Error responses

Every error, from any endpoint, has this shape:

```json
{
  "error": {
    "code": "insufficient_stock",
    "message": "Insufficient stock. Product B: requested 1, available 0.",
    "details": [
      {
        "field": "items.1.quantity",
        "message": "Product B: requested 1, available 0."
      }
    ]
  }
}
```

| HTTP | `code`                                                                                   | Raised by                                                                               |
| ---- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| 404  | `not_found`                                                                              | `NotFoundError`, unknown routes                                                         |
| 409  | `conflict`, `insufficient_stock`, `invalid_status_transition`, `order_already_cancelled` | `ConflictError` and subclasses                                                          |
| 422  | `validation_error`                                                                       | Pydantic request validation; `details` lists each field                                 |
| 500  | `internal_error`                                                                         | Any unexpected exception. The message is generic; the stack trace goes only to the log. |

Messages are written for store staff and are shown in the UI as they are.

---

## Business rules

| Rule                                                              | Where it is enforced                                                                                                   |
| ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Cart cannot be empty; quantity is a positive whole number         | `orders/schemas.py` (`OrderCreate`)                                                                                    |
| Prices and totals come from the server                            | `OrderItemCreate` has no price fields and forbids extra fields; `_build_order()` reads prices from locked product rows |
| Product must exist                                                | `_ensure_all_products_exist()` → 404                                                                                   |
| Stock must be sufficient for every line, or the whole order fails | `_ensure_sufficient_stock()` → 409 before anything is written                                                          |
| Unit price and name are snapshots                                 | `OrderItem.product_name`, `OrderItem.unit_price`                                                                       |
| Only valid status transitions                                     | `orders/status_rules.py` (`ALLOWED_TRANSITIONS`), checked in `fulfilment_service.py`                                   |
| Stock is restored exactly once                                    | Order row lock + state machine: a second cancel sees `CANCELLED` and is rejected                                       |
| Stock and prices can never be negative                            | Database `CHECK` constraints                                                                                           |
| Low-stock threshold                                               | `LOW_STOCK_THRESHOLD` setting, applied by `classify_stock()` and the dashboard query                                   |

---

## Transactions and concurrency

**Placing an order** (`orders/service.py → create_order`):

```python
with session.begin():
    products = lock_products_by_ids(...)   # SELECT ... FOR UPDATE ORDER BY id
    _ensure_all_products_exist(...)        # 404 → rollback
    _ensure_sufficient_stock(...)          # 409 → rollback
    _deduct_stock(...)
    add_order(...)                         # order + items inserted
# commit: stock deduction and order become visible together
```

**Changing status / cancelling** (`orders/fulfilment_service.py → update_order_status`):

```python
with session.begin():
    order = lock_order(...)                # SELECT ... FOR UPDATE on the order row
    _ensure_transition_allowed(...)        # 409 → rollback
    if cancelling: _restore_stock(...)     # product rows locked in id order
    order.status = target
```

- Two orders for the last unit: the second waits for the first lock, then reads the updated
  stock and gets `409`.
- Two cancellations of the same order: the second waits, then reads `CANCELLED` and gets `409`.
- Both paths lock product rows in id order, so they cannot deadlock each other.
- Success is logged only after the commit.

---

## Module and function reference

### `app/core`

| Function / class                                                                       | Signature                                                                                     | Purpose                                                                           |
| -------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `get_settings`                                                                         | `() -> Settings`                                                                              | Reads settings once from env / `.env` (cached).                                   |
| `Settings`                                                                             | fields: `database_url`, `environment`, `low_stock_threshold`, `cors_origins`, `api_v1_prefix` | Typed configuration.                                                              |
| `AppError`                                                                             | `(message: str, details: list[ErrorDetail] \| None = None)`                                   | Base for expected errors; carries `status_code` and `code`.                       |
| `NotFoundError`, `ConflictError`                                                       | subclasses of `AppError`                                                                      | 404 / 409.                                                                        |
| `InsufficientStockError`, `InvalidStatusTransitionError`, `OrderAlreadyCancelledError` | subclasses of `ConflictError`                                                                 | 409 with a specific `code`.                                                       |
| `register_exception_handlers`                                                          | `(app: FastAPI) -> None`                                                                      | Installs the handlers that produce the standard error JSON.                       |
| `ErrorResponse`                                                                        | `{error: ErrorBody}`                                                                          | The error schema, used by handlers and in OpenAPI.                                |
| `error_responses`                                                                      | `(*status_codes: int) -> dict`                                                                | Builds a route's `responses=` for Swagger, e.g. `error_responses(404, 409, 422)`. |
| `setup_logging`                                                                        | `(environment: str) -> None`                                                                  | Configures handlers and formatters for the environment.                           |
| `log_with_context`                                                                     | `(logger, level, message, context=None, exc_info=None, **kwargs) -> None`                     | The single logging call used across the app.                                      |
| `request_id_var`                                                                       | `ContextVar[str \| None]`                                                                     | Current request ID, added to every log line.                                      |
| `RequestContextMiddleware`                                                             | ASGI middleware                                                                               | Sets the request ID, adds `X-Request-ID`, writes the access log.                  |

### `app/db`

| Name                                    | Purpose                                                          |
| --------------------------------------- | ---------------------------------------------------------------- |
| `engine`, `SessionLocal`                | Connection pool and session factory.                             |
| `get_db() -> Iterator[Session]`         | One session per request, always closed.                          |
| `DbSession`                             | `Annotated[Session, Depends(get_db)]`, used in route signatures. |
| `Base`                                  | Declarative base with deterministic constraint names.            |
| `UUIDPrimaryKeyMixin`, `TimestampMixin` | Shared `id`, `created_at`, `updated_at` columns.                 |

### `app/products`

| Function                    | Signature                                                 | Purpose                                                             |
| --------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------- |
| `crud.list_products`        | `(session) -> Sequence[Product]`                          | All products sorted by name, then SKU.                              |
| `crud.get_product`          | `(session, product_id) -> Product \| None`                | Primary-key lookup.                                                 |
| `crud.lock_products_by_ids` | `(session, product_ids) -> list[Product]`                 | `SELECT ... FOR UPDATE ORDER BY id`. Must run inside a transaction. |
| `service.list_products`     | `(session) -> ProductListResponse`                        | Catalogue response.                                                 |
| `service.get_product`       | `(session, product_id) -> ProductRead`                    | Raises `NotFoundError` if missing.                                  |
| `stock.classify_stock`      | `(quantity: int, low_stock_threshold: int) -> StockLevel` | `0` → out of stock, `1..threshold` → low, above → in stock.         |

### `app/orders`

| Function                                         | Signature                                                                   | Purpose                                                           |
| ------------------------------------------------ | --------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `service.create_order`                           | `(session, payload: OrderCreate) -> OrderRead`                              | Atomic placement: lock, validate, deduct, insert.                 |
| `service.get_order`                              | `(session, order_id) -> OrderRead`                                          | Raises `NotFoundError` if missing.                                |
| `service.get_order_by_reference`                 | `(session, order_reference: str) -> OrderRead`                              | Trims and upper-cases, then exact match.                          |
| `service.list_orders`                            | `(session, *, reference, status, page, page_size) -> OrderListResponse`     | Filtered, paginated list with totals.                             |
| `service.generate_order_reference`               | `() -> str`                                                                 | `ORD-YYYYMMDD-XXXXXX`, random suffix from `secrets`.              |
| `fulfilment_service.update_order_status`         | `(session, order_id, target: OrderStatus) -> OrderRead`                     | Locks the order, checks the transition, restores stock on cancel. |
| `status_rules.can_transition`                    | `(current, target) -> bool`                                                 | Single source of truth for transitions.                           |
| `status_rules.allowed_next_statuses`             | `(current) -> tuple[OrderStatus, ...]`                                      | Feeds `allowed_transitions` in responses.                         |
| `crud.add_order`                                 | `(session, order) -> Order`                                                 | Inserts order and items, flushes.                                 |
| `crud.get_order` / `crud.get_order_by_reference` | `(session, …) -> Order \| None`                                             | Loads items with `selectinload`.                                  |
| `crud.lock_order`                                | `(session, order_id) -> Order \| None`                                      | `SELECT ... FOR UPDATE` on the order row.                         |
| `crud.list_orders`                               | `(session, *, reference, status, limit, offset) -> list[tuple[Order, int]]` | Newest first, with item count from a SQL subquery.                |
| `crud.count_orders`                              | `(session, *, reference, status) -> int`                                    | Total for pagination, same filters as the list.                   |

### `app/dashboard`

| Function                             | Signature                                                | Purpose                                          |
| ------------------------------------ | -------------------------------------------------------- | ------------------------------------------------ |
| `crud.count_orders_by_status`        | `(session) -> dict[OrderStatus, int]`                    | `GROUP BY status`.                               |
| `crud.count_products_by_stock_level` | `(session, low_stock_threshold) -> tuple[int, int, int]` | Total, low and out-of-stock counts in one query. |
| `service.get_summary`                | `(session, low_stock_threshold) -> DashboardSummary`     | Fills missing statuses with 0.                   |

### `scripts`

| Function                                        | Purpose                                                                            |
| ----------------------------------------------- | ---------------------------------------------------------------------------------- |
| `seed.seed_products() -> int`                   | Inserts missing products (`ON CONFLICT (sku) DO NOTHING`); checks SKUs are unique. |
| `seed_data.build_seed_products() -> list[dict]` | The 58 sample products, prices as `Decimal`.                                       |

---

## Logging

Three levels only: **INFO** (startup, shutdown, requests, orders created, stock deducted or
restored, status changes), **WARNING** (expected rejections: 404, 409, 422) and **ERROR**
(500s and unexpected failures, with stack trace).

```python
log_with_context(
    logger,
    "INFO",
    "ORDERS: Order created (service.py create_order)",
    context={"order_reference": order.order_reference, "total_amount": order.total_amount},
)
```

- Message format: `"FEATURE: What happened (file.py function)"`; data goes in `context`.
- The request ID is added automatically to every line of a request.
- `ENVIRONMENT=development`: readable console output, plus pretty-JSON files in `backend/logs/`
  (`info.log`, `access.log`, `warn.log`, `error.log`, rotated at 50 MB).
- Any other environment: one JSON object per line on stdout.

---

## Testing

```bash
uv run pytest                      # 120 tests
uv run pytest tests/unit           # pure logic, no database
uv run pytest tests/integration    # API + PostgreSQL
```

| File                                                  | What it covers                                                                                             |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `unit/test_status_rules.py`                           | All 16 status combinations against the allowed transitions                                                 |
| `unit/test_stock_levels.py`                           | Stock level boundaries (0, 1, 5, 6)                                                                        |
| `unit/test_error_handlers.py`, `unit/test_logging.py` | Error JSON shape; log formatters                                                                           |
| `unit/test_health.py`                                 | Health endpoint                                                                                            |
| `integration/test_request_logging.py`                 | `X-Request-ID` handling, access log line, WARNING for rejections                                           |
| `integration/test_products_api.py`                    | Product list and detail, price format, 404/422                                                             |
| `integration/test_create_order.py`                    | Placement, totals, stock deduction, both 409 paths, 404, every 422 case, price snapshot, concurrent orders |
| `integration/test_list_orders.py`                     | Search, wildcard safety, status filter, pagination                                                         |
| `integration/test_get_order.py`                       | Detail by id and by reference                                                                              |
| `integration/test_order_status.py`                    | Valid transitions, every invalid transition, cancellation, double cancellation, concurrent cancellations   |
| `integration/test_dashboard.py`                       | Counts by status and stock thresholds                                                                      |
| `integration/test_persistence.py`                     | Orders and stock survive a real restart of the API process                                                 |
| `integration/test_openapi_docs.py`                    | Swagger documents the real error shape                                                                     |

How the suite is isolated:

- `tests/conftest.py` sets `DATABASE_URL` to `TEST_DATABASE_URL` before the app is imported and
  stops if the database name does not end in `_test`.
- The schema is built from the real Alembic migrations once per run.
- Every test starts from empty tables (`TRUNCATE`), so tests do not depend on each other's order.
- Concurrency tests use real threads and real sessions, with a short pause injected to make the
  race window reliable.

---

## Adding a new feature

1. Create `app/<feature>/` with `models.py`, `schemas.py`, `crud.py`, `service.py`, `router.py`.
2. Import new models in `app/db/all_models.py`, then
   `uv run alembic revision --autogenerate -m "..."` and review the generated file.
3. Register the router in `app/main.py`.
4. Raise `AppError` subclasses for expected failures; declare them with `error_responses(...)`.
5. Put writes inside `with session.begin():` in the service; keep `crud.py` free of commits.
6. Log with `log_with_context`; add integration tests against the test database.
