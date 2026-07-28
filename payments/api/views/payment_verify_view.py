from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from payments.api.serializers import (
    PaymentSerializer,
    VerifyPaymentSerializer,
)
from payments.models import Payment
from payments.services.payment_verify_service import (
    PaymentVerifyService,
)


class VerifyPaymentView(
    generics.GenericAPIView
):
    """
    تأیید پرداخت آزمایشی.

    POST /api/payments/verify/
    """

    permission_classes = [IsAuthenticated]
    serializer_class = VerifyPaymentSerializer

    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        input_serializer = self.get_serializer(
            data=request.data,
        )

        input_serializer.is_valid(
            raise_exception=True,
        )

        payment = get_object_or_404(
            Payment.objects.select_related(
                "order",
            ),
            id=input_serializer.validated_data[
                "payment_id"
            ],
            order__user=request.user,
        )

        result = PaymentVerifyService(
            payment=payment,
            authority=input_serializer.validated_data[
                "authority"
            ],
            mock_status=input_serializer.validated_data[
                "mock_status"
            ],
        ).run()

        response_status = (
            status.HTTP_200_OK
            if result.payment.is_successful
            else status.HTTP_400_BAD_REQUEST
        )

        return Response(
            {
                "message": result.message,
                "payment": PaymentSerializer(
                    result.payment,
                    context={
                        "request": request,
                    },
                ).data,
            },
            status=response_status,
        )
