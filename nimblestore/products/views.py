from rest_framework import mixins, viewsets

from .models import Product
from .serializers import ProductSerializer


class ProductViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    # Disallow full PUT replacement; only PATCH (partial update) is exposed
    http_method_names = ["get", "post", "patch", "head", "options"]
