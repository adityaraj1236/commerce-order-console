"""Point the application at the test database before any app module is imported."""

import os

from sqlalchemy.engine import make_url

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://postgres:password@localhost:5434/commerce_console_test",
)

if not (make_url(TEST_DATABASE_URL).database or "").endswith("_test"):
    raise RuntimeError(
        f"Refusing to run tests against non-test database: {make_url(TEST_DATABASE_URL)!r}"
    )

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
# Log as JSON to stdout during tests instead of writing development log files.
os.environ["ENVIRONMENT"] = "test"
