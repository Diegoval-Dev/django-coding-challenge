from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from products.models import Product

from .exceptions import InsufficientStockError, OrderNotCancellableError
from .models import Order
from .serializers import OrderSerializer, PlaceOrderSerializer
from .services import cancel_order, place_order


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Order.objects.prefetch_related("items__product").all()
    serializer_class = OrderSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return PlaceOrderSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = PlaceOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = place_order(serializer.validated_data["items"])
        except Product.DoesNotExist:
            return Response(
                {"error": "One or more products were not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except InsufficientStockError as exc:
            return Response(
                {
                    "error": str(exc),
                    "product": exc.product_name,
                    "available": exc.available,
                    "requested": exc.requested,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        order = self.get_object()

        try:
            order = cancel_order(order)
        except OrderNotCancellableError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(OrderSerializer(order).data)
