"""
Concurrency test: two simultaneous orders must not oversell a product.

This test uses Python threads to simulate two requests arriving at the
same time for the last unit of a product. Only one should succeed.

Implementation note on test reliability:
  - We use a threading.Barrier to force both threads past the setup phase
    before either makes its HTTP request, maximising the window of overlap.
  - The test is marked transaction=True so pytest-django uses real DB
    transactions instead of the default test-wrapping savepoints — this
    is required for select_for_update() locking to behave correctly across
    threads (each thread opens its own connection).
  - On a heavily loaded CI machine the threads may not fully overlap, but
    the test is still valuable: if locking is missing, this test will
    flake and catch the bug. If locking is correct, it always passes.
"""

import threading

import pytest
from rest_framework.test import APIClient

from products.models import Product


@pytest.mark.django_db(transaction=True)
def test_concurrent_orders_do_not_oversell():
    """
    Given a product with stock=1, two simultaneous orders for quantity=1
    must result in exactly one success (201) and one failure (400).
    The final stock must be 0, not -1.
    """
    product = Product.objects.create(name="Last Item", price="10.00", stock=1)

    results = []
    barrier = threading.Barrier(2)  # both threads must reach here before proceeding

    def attempt_purchase():
        # Each thread gets its own APIClient (and therefore its own DB connection).
        client = APIClient()
        barrier.wait()  # synchronise to maximise concurrency overlap
        response = client.post(
            "/api/orders/",
            {"items": [{"product_id": product.pk, "quantity": 1}]},
            format="json",
        )
        results.append(response.status_code)

    threads = [threading.Thread(target=attempt_purchase) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Exactly one order succeeded and one was rejected.
    assert results.count(201) == 1, f"Expected 1 success, got: {results}"
    assert results.count(400) == 1, f"Expected 1 rejection, got: {results}"

    # The product stock must be exactly 0 — no phantom negative stock.
    product.refresh_from_db()
    assert product.stock == 0


@pytest.mark.django_db(transaction=True)
def test_concurrent_cancels_restore_stock_exactly_once():
    """
    Two simultaneous cancel requests for the same pending order must result
    in the stock being restored exactly once, not twice.
    """
    product = Product.objects.create(name="Item", price="5.00", stock=10)

    # Place an order that consumes 3 units.
    client = APIClient()
    response = client.post(
        "/api/orders/",
        {"items": [{"product_id": product.pk, "quantity": 3}]},
        format="json",
    )
    order_id = response.data["id"]

    results = []
    barrier = threading.Barrier(2)

    def attempt_cancel():
        c = APIClient()
        barrier.wait()
        resp = c.post(f"/api/orders/{order_id}/cancel/")
        results.append(resp.status_code)

    threads = [threading.Thread(target=attempt_cancel) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # One cancel succeeds, one is rejected (already cancelled).
    assert 200 in results
    assert 400 in results

    # Stock is restored exactly once: 10 - 3 + 3 = 10.
    product.refresh_from_db()
    assert product.stock == 10
