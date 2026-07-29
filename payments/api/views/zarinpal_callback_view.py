from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.response import Response

from payments.api.serializers import (
    PaymentSerializer,
    ZarinpalCallbackSerializer,
)
from payments.models import Payment
from payments.services.zarinpal_callback_service import (
    ZarinpalCallbackService,
)


class ZarinpalCallbackView(
    generics.GenericAPIView
):
    """
    تأیید بازگشت پرداخت واقعی زرین‌پال.

    POST /api/payments/callback/zarinpal/

    Body:
    {
        "authority": "A000...",
        "status": "OK"
    }
    """

    permission_classes = [
        IsAuthenticated,
    ]

    serializer_class = (
        ZarinpalCallbackSerializer
    )

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

        authority = (
            input_serializer
            .validated_data["authority"]
        )

        callback_status = (
            input_serializer
            .validated_data["status"]
        )

        payment = get_object_or_404(
            Payment.objects.select_related(
                "order",
            ),
            authority=authority,
            gateway="zarinpal",
            order__user=request.user,
        )

        try:
            result = ZarinpalCallbackService(
                payment=payment,
                authority=authority,
                callback_status=(
                    callback_status
                ),
            ).run()

        except ValueError as error:
            return Response(
                {
                    "error": str(error),
                },
                status=(
                    status
                    .HTTP_400_BAD_REQUEST
                ),
            )

        response_status = (
            status.HTTP_200_OK
            if result.is_successful
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
