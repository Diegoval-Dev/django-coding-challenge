"""
Order business logic lives here, not in views.

Keeping placement and cancellation in a service layer means:
  - The logic is testable without an HTTP stack.
  - Views stay thin: validate input → call service → serialize output.
  - The transaction boundary is explicit and co-located with the
    operations it protects.
"""

from django.db import transaction
from django.db.models import F

from products.models import Product

from .exceptions import InsufficientStockError, OrderNotCancellableError
from .models import Order, OrderItem, OrderStatus


def place_order(items: list[dict]) -> Order:
    """
    Create a new Order from a list of {product_id, quantity} dicts.

    Concurrency strategy — pessimistic locking:
      SELECT ... FOR UPDATE acquires a row-level lock on each Product row
      before checking stock. Any concurrent transaction attempting the
      same lock will block until the first one commits or rolls back.
      This guarantees that two simultaneous orders for the last unit of a
      product cannot both succeed (only one sees stock >= 1; the other
      sees 0 and gets an InsufficientStockError).

    Price lock:
      unit_price is copied from product.price at placement time.
      Future changes to Product.price do not affect this order.

    Raises:
        Product.DoesNotExist  – if any product_id is invalid.
        InsufficientStockError – if stock is insufficient for any item.
    """
    with transaction.atomic():
        order = Order.objects.create(status=OrderStatus.PENDING)

        for item_data in items:
            # select_for_update() holds the lock until the transaction ends,
            # preventing concurrent reads from observing stale stock values.
            product = (
                Product.objects.select_for_update().get(pk=item_data["product_id"])
            )
            quantity = item_data["quantity"]

            if product.stock < quantity:
                raise InsufficientStockError(
                    product_name=product.name,
                    available=product.stock,
                    requested=quantity,
                )

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=product.price,  # price snapshot
            )

            product.stock -= quantity
            product.save(update_fields=["stock"])

        return order


def cancel_order(order: Order) -> Order:
    """
    Transition an Order from 'pending' to 'cancelled' and restore stock.

    We re-fetch the order inside a transaction with select_for_update to
    guard against a race where two cancel requests arrive simultaneously
    for the same order.

    Raises:
        OrderNotCancellableError – if the order is fulfilled or already cancelled.
    """
    with transaction.atomic():
        # Re-fetch inside the transaction to get the authoritative status.
        order = Order.objects.select_for_update().get(pk=order.pk)

        if order.status == OrderStatus.FULFILLED:
            raise OrderNotCancellableError("A fulfilled order cannot be cancelled.")
        if order.status == OrderStatus.CANCELLED:
            raise OrderNotCancellableError("This order is already cancelled.")

        for item in order.items.all():
            # Use F() for an atomic SQL UPDATE so we don't read stock into
            # Python first — avoids a lost-update if another transaction
            # modifies stock between our read and write.
            Product.objects.filter(pk=item.product_id).update(
                stock=F("stock") + item.quantity
            )

        order.status = OrderStatus.CANCELLED
        order.save(update_fields=["status"])

        return order
