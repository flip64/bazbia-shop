from django.shortcuts import get_object_or_404
from rest_framework import generics

from products.models import Product
from community.models import ProductReview
from community.api.mixins import PublicReadAuthenticatedWriteMixin
from community.api.serializers import ProductReviewSerializer


class ProductReviewListCreateAPIView(PublicReadAuthenticatedWriteMixin, generics.ListCreateAPIView):
    serializer_class = ProductReviewSerializer

    def get_product(self):
        if not hasattr(self, "_product"):
            self._product = get_object_or_404(Product, slug=self.kwargs["slug"], is_active=True)

        return self._product

    def get_queryset(self):
        return ProductReview.objects.filter(
            product=self.get_product(),
            status=ProductReview.STATUS_APPROVED,
        ).select_related("user", "product").order_by("-created_at")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["product"] = self.get_product()
        return context