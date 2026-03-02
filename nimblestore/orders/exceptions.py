class InsufficientStockError(Exception):
    """Raised when a product does not have enough stock to fulfil a requested quantity."""

    def __init__(self, product_name: str, available: int, requested: int):
        self.product_name = product_name
        self.available = available
        self.requested = requested
        super().__init__(
            f"Insufficient stock for '{product_name}': "
            f"{available} available, {requested} requested."
        )


class OrderNotCancellableError(Exception):
    """Raised when an order cannot transition to 'cancelled'."""
