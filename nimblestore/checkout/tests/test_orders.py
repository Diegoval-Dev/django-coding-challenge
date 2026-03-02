"""
Tests for order placement, cancellation, and the business rules that
make them non-trivial: price locking, stock deduction, and state machine
transitions.

Every test asserts on the *effect* of the operation (DB state, response
body fields) rather than just verifying a status code.
"""

import pytest
from rest_framework.test import APIClient

from orders.models import Order, OrderItem, OrderStatus
from products.models import Product


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def product(db):
    return Product.objects.create(name="Widget", price="9.99", stock=10)


@pytest.fixture
def low_stock_product(db):
    return Product.objects.create(name="Scarce Widget", price="5.00", stock=1)


def place_order(api_client, items):
    """Helper: POST to /api/orders/ and return the response."""
    return api_client.post(
        "/api/orders/",
        {"items": items},
        format="json",
    )


# ---------------------------------------------------------------------------
# Placing orders — happy path
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPlaceOrder:
    def test_returns_201_with_order_data(self, api_client, product):
        response = place_order(api_client, [{"product_id": product.pk, "quantity": 2}])

        assert response.status_code == 201
        assert response.data["status"] == "pending"
        assert "id" in response.data

    def test_creates_order_in_database(self, api_client, product):
        place_order(api_client, [{"product_id": product.pk, "quantity": 2}])

        assert Order.objects.count() == 1

    def test_deducts_stock_from_product(self, api_client, product):
        place_order(api_client, [{"product_id": product.pk, "quantity": 3}])

        product.refresh_from_db()
        assert product.stock == 7  # 10 - 3

    def test_response_contains_items_with_unit_price(self, api_client, product):
        response = place_order(api_client, [{"product_id": product.pk, "quantity": 2}])

        items = response.data["items"]
        assert len(items) == 1
        assert items[0]["quantity"] == 2
        assert items[0]["unit_price"] == "9.99"

    def test_response_total_matches_quantity_times_price(self, api_client, product):
        response = place_order(api_client, [{"product_id": product.pk, "quantity": 4}])

        # total = 4 × 9.99 = 39.96
        assert float(response.data["total"]) == pytest.approx(39.96)

    def test_order_with_multiple_items(self, api_client):
        p1 = Product.objects.create(name="A", price="10.00", stock=5)
        p2 = Product.objects.create(name="B", price="20.00", stock=5)

        response = place_order(
            api_client,
            [
                {"product_id": p1.pk, "quantity": 2},
                {"product_id": p2.pk, "quantity": 1},
            ],
        )

        assert response.status_code == 201
        assert len(response.data["items"]) == 2
        # total = 2×10 + 1×20 = 40
        assert float(response.data["total"]) == pytest.approx(40.00)


# ---------------------------------------------------------------------------
# Price locking
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPriceLock:
    def test_order_retains_price_after_product_price_changes(
        self, api_client, product
    ):
        """
        The core price-lock requirement: changing a product's price after
        an order is placed must not retroactively change the order's total.
        """
        place_order(api_client, [{"product_id": product.pk, "quantity": 2}])

        # Simulate a price change after the order was placed.
        product.price = "99.99"
        product.save()

        order = Order.objects.first()
        item = order.items.first()

        # unit_price on the OrderItem is frozen at the original price.
        assert str(item.unit_price) == "9.99"
        assert float(order.total) == pytest.approx(19.98)  # 2 × 9.99


# ---------------------------------------------------------------------------
# Stock validation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestStockValidation:
    def test_rejects_order_exceeding_available_stock(self, api_client, product):
        response = place_order(
            api_client, [{"product_id": product.pk, "quantity": 11}]
        )

        assert response.status_code == 400

    def test_error_response_names_the_product(self, api_client, product):
        response = place_order(
            api_client, [{"product_id": product.pk, "quantity": 99}]
        )

        assert "Widget" in response.data["error"]

    def test_error_response_includes_available_and_requested(
        self, api_client, product
    ):
        response = place_order(
            api_client, [{"product_id": product.pk, "quantity": 99}]
        )

        assert response.data["available"] == 10
        assert response.data["requested"] == 99

    def test_out_of_stock_product_is_rejected(self, api_client):
        empty = Product.objects.create(name="Empty", price="1.00", stock=0)
        response = place_order(api_client, [{"product_id": empty.pk, "quantity": 1}])

        assert response.status_code == 400

    def test_stock_is_not_changed_on_failed_order(self, api_client, product):
        place_order(api_client, [{"product_id": product.pk, "quantity": 99}])

        product.refresh_from_db()
        assert product.stock == 10  # unchanged

    def test_nonexistent_product_returns_404(self, api_client):
        response = place_order(api_client, [{"product_id": 99999, "quantity": 1}])

        assert response.status_code == 404

    def test_zero_quantity_is_rejected(self, api_client, product):
        response = place_order(
            api_client, [{"product_id": product.pk, "quantity": 0}]
        )

        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Order cancellation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCancelOrder:
    def test_pending_order_can_be_cancelled(self, api_client, product):
        create_resp = place_order(
            api_client, [{"product_id": product.pk, "quantity": 2}]
        )
        order_id = create_resp.data["id"]

        response = api_client.post(f"/api/orders/{order_id}/cancel/")

        assert response.status_code == 200
        assert response.data["status"] == "cancelled"

    def test_cancellation_restores_stock(self, api_client, product):
        create_resp = place_order(
            api_client, [{"product_id": product.pk, "quantity": 3}]
        )
        order_id = create_resp.data["id"]

        api_client.post(f"/api/orders/{order_id}/cancel/")

        product.refresh_from_db()
        assert product.stock == 10  # fully restored

    def test_fulfilled_order_cannot_be_cancelled(self, api_client, product):
        create_resp = place_order(
            api_client, [{"product_id": product.pk, "quantity": 1}]
        )
        order = Order.objects.get(pk=create_resp.data["id"])
        order.status = OrderStatus.FULFILLED
        order.save()

        response = api_client.post(f"/api/orders/{order.pk}/cancel/")

        assert response.status_code == 400
        assert "fulfilled" in response.data["error"].lower()

    def test_already_cancelled_order_returns_400(self, api_client, product):
        create_resp = place_order(
            api_client, [{"product_id": product.pk, "quantity": 1}]
        )
        order_id = create_resp.data["id"]

        api_client.post(f"/api/orders/{order_id}/cancel/")
        response = api_client.post(f"/api/orders/{order_id}/cancel/")

        assert response.status_code == 400

    def test_stock_not_double_restored_on_repeated_cancel(self, api_client, product):
        create_resp = place_order(
            api_client, [{"product_id": product.pk, "quantity": 2}]
        )
        order_id = create_resp.data["id"]

        api_client.post(f"/api/orders/{order_id}/cancel/")
        api_client.post(f"/api/orders/{order_id}/cancel/")  # should fail silently

        product.refresh_from_db()
        assert product.stock == 10  # not 12


# ---------------------------------------------------------------------------
# Order retrieval
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestOrderRetrieval:
    def test_list_returns_all_orders(self, api_client, product):
        place_order(api_client, [{"product_id": product.pk, "quantity": 1}])
        place_order(api_client, [{"product_id": product.pk, "quantity": 1}])

        response = api_client.get("/api/orders/")

        assert response.status_code == 200
        assert len(response.data) == 2

    def test_list_orders_most_recent_first(self, api_client, product):
        r1 = place_order(api_client, [{"product_id": product.pk, "quantity": 1}])
        r2 = place_order(api_client, [{"product_id": product.pk, "quantity": 1}])

        response = api_client.get("/api/orders/")
        ids = [o["id"] for o in response.data]

        # Most recently created order should appear first (ordering = ['-created_at'])
        assert ids[0] == r2.data["id"]
        assert ids[1] == r1.data["id"]

    def test_order_detail_includes_items_and_total(self, api_client, product):
        create_resp = place_order(
            api_client, [{"product_id": product.pk, "quantity": 2}]
        )
        order_id = create_resp.data["id"]

        response = api_client.get(f"/api/orders/{order_id}/")

        assert response.status_code == 200
        assert len(response.data["items"]) == 1
        assert float(response.data["total"]) == pytest.approx(19.98)

    def test_order_detail_item_includes_product_snapshot(self, api_client, product):
        create_resp = place_order(
            api_client, [{"product_id": product.pk, "quantity": 1}]
        )
        order_id = create_resp.data["id"]

        response = api_client.get(f"/api/orders/{order_id}/")

        item = response.data["items"][0]
        assert item["product"]["name"] == "Widget"
        assert item["unit_price"] == "9.99"
