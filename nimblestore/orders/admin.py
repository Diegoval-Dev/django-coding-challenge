from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["unit_price", "line_total"]

    def line_total(self, obj):
        return obj.line_total

    line_total.short_description = "Line total"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "status", "created_at"]
    list_filter = ["status"]
    inlines = [OrderItemInline]
    readonly_fields = ["created_at"]
