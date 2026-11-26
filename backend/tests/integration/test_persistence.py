"""Orders and stock must survive an application restart.

These tests run the real API in a separate uvicorn process against the test database,
write data through HTTP, kill the process (no graceful shutdown), start a brand-new
process and read the data back. Nothing can survive in Python memory between the two.
"""

import os
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import httpx

from app.products.models import Product

BACKEND_DIR = Path(__file__).resolve().parents[2]
STARTUP_TIMEOUT_SECONDS = 30


@contextmanager
def running_api_server(port: int) -> Iterator[httpx.Client]:
    """Start `uvicorn app.main:app` as a separate process; kill it on exit."""
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port)],
        cwd=BACKEND_DIR,
        env=os.environ.copy(),  # tests/conftest.py already points DATABASE_URL at the test DB
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{port}/api/v1", timeout=10) as client:
            _wait_until_healthy(client, process)
            yield client
    finally:
        process.kill()
        process.wait(timeout=10)


def _wait_until_healthy(client: httpx.Client, process: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"API server exited early with code {process.returncode}")
        try:
            if client.get("/health").status_code == 200:
                return
        except httpx.TransportError:
            pass
        time.sleep(0.2)
    raise TimeoutError("API server did not become healthy in time")


def _place_order(client: httpx.Client, product: Product, quantity: int) -> dict[str, Any]:
    body = {"items": [{"product_id": str(product.id), "quantity": quantity}]}
    response = client.post("/orders", json=body)
    assert response.status_code == 201, response.text
    order: dict[str, Any] = response.json()
    return order


def test_orders_and_stock_survive_an_application_restart(
    create_product: Callable[..., Product], free_tcp_port_factory: Callable[[], int]
) -> None:
    product = create_product(name="Product A", stock_quantity=5)

    # ---- first application process: write data, then kill it
    with running_api_server(free_tcp_port_factory()) as api:
        kept_order = _place_order(api, product, 2)
        cancelled_order = _place_order(api, product, 1)
        cancel = api.patch(f"/orders/{cancelled_order['id']}/status", json={"status": "CANCELLED"})
        assert cancel.status_code == 200
        assert api.get(f"/products/{product.id}").json()["stock_quantity"] == 3

    # ---- brand-new application process: everything must still be there
    with running_api_server(free_tcp_port_factory()) as api:
        stored_kept = api.get(f"/orders/{kept_order['id']}").json()
        stored_cancelled = api.get(f"/orders/reference/{cancelled_order['order_reference']}").json()
        stock_after_restart = api.get(f"/products/{product.id}").json()["stock_quantity"]
        listed = api.get("/orders").json()

        # Orders, their items and statuses survived.
        assert stored_kept == kept_order
        assert stored_cancelled["status"] == "CANCELLED"
        assert listed["total"] == 2

        # Stock survived: 5 - 2 (kept order) = 3; the cancelled order's unit was restored.
        assert stock_after_restart == 3

        # The "restore exactly once" guarantee also survives the restart.
        repeat = api.patch(f"/orders/{cancelled_order['id']}/status", json={"status": "CANCELLED"})
        assert repeat.status_code == 409
        assert api.get(f"/products/{product.id}").json()["stock_quantity"] == 3
