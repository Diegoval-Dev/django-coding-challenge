from django.db import models


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    FULFILLED = "fulfilled", "Fulfilled"
    CANCELLED = "cancelled", "Cancelled"


class Order(models.Model):
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} ({self.status})"

    @property
    def total(self):
        return sum(item.line_total for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(
        "products.Product",
        related_name="order_items",
        on_delete=models.PROTECT,
    )
    quantity = models.PositiveIntegerField()
    # Snapshot of the product price at the moment the order was placed.
    # This is intentionally decoupled from products.Product.price so that
    # a subsequent price change never retroactively affects this order.
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def line_total(self):
        return self.unit_price * self.quantity
