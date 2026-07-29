# payments/api/views/payment_detail_view.py

from rest_framework import generics
from rest_framework.permissions import (
    IsAuthenticated,
)

from payments.api.serializers import (
    PaymentSerializer,
)
from payments.models import Payment


class PaymentDetailView(
    generics.RetrieveAPIView
):
    """
    دریافت جزئیات یک پرداخت متعلق به کاربر واردشده.

    Endpoint:
        GET /api/payments/<payment_id>/
    """

    permission_classes = [
        IsAuthenticated,
    ]

    serializer_class = PaymentSerializer

    lookup_field = "id"
    lookup_url_kwarg = "payment_id"

    def get_queryset(self):
        return (
            Payment.objects
            .select_related("order")
            .filter(
                order__user=self.request.user,
            )
        )
