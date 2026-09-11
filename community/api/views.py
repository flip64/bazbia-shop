from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)

from products.models import Product

from community.models import (
    ProductReview,
    ProductQuestion,
)

from community.api.serializers import (
    ProductReviewSerializer,
    ProductQuestionSerializer,
    ProductAnswerSerializer,
)


# =========================================================
# Permission Mixin
# GET  -> عمومی
# POST -> فقط کاربر واردشده
# =========================================================
class PublicReadAuthenticatedWriteMixin:
    """
    مشاهده محتوا برای همه آزاد است.

    ثبت محتوا فقط برای کاربران واردشده مجاز است.
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]

        return [IsAuthenticated()]


# =========================================================
# Product Reviews
# =========================================================
class ProductReviewListCreateAPIView(
    PublicReadAuthenticatedWriteMixin,
    generics.ListCreateAPIView,
):
    serializer_class = ProductReviewSerializer

    def get_product(self):
        if not hasattr(self, "_product"):
            self._product = get_object_or_404(
                Product,
                slug=self.kwargs["slug"],
                is_active=True,
            )

        return self._product

    def get_queryset(self):
        return (
            ProductReview.objects
            .filter(
                product=self.get_product(),
                status=ProductReview.STATUS_APPROVED,
            )
            .select_related(
                "user",
                "product",
            )
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()

        context["product"] = self.get_product()

        return context


# =========================================================
# Product Questions
# =========================================================
class ProductQuestionListCreateAPIView(
    PublicReadAuthenticatedWriteMixin,
    generics.ListCreateAPIView,
):
    serializer_class = ProductQuestionSerializer

    def get_product(self):
        if not hasattr(self, "_product"):
            self._product = get_object_or_404(
                Product,
                slug=self.kwargs["slug"],
                is_active=True,
            )

        return self._product

    def get_queryset(self):
        return (
            ProductQuestion.objects
            .filter(
                product=self.get_product(),
                status=ProductQuestion.STATUS_APPROVED,
            )
            .select_related(
                "user",
                "product",
            )
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()

        context["product"] = self.get_product()

        return context


# =========================================================
# Product Answers
# =========================================================
class ProductAnswerCreateAPIView(
    generics.CreateAPIView,
):
    serializer_class = ProductAnswerSerializer
    permission_classes = [IsAuthenticated]

    def get_question(self):
        if not hasattr(self, "_question"):
            self._question = get_object_or_404(
                ProductQuestion.objects.select_related(
                    "product",
                ),
                id=self.kwargs["question_id"],
                status=ProductQuestion.STATUS_APPROVED,
            )

        return self._question

    def get_serializer_context(self):
        context = super().get_serializer_context()

        context["question"] = self.get_question()

        return context