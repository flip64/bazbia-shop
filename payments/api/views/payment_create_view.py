from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from orders.models import Order
from payments.api.serializers import (
    CreatePaymentSerializer,
    PaymentSerializer,
)
from payments.services.payment_create_service import (
    PaymentCreateService,
)


class CreatePaymentView(
    generics.GenericAPIView
):
    """
    ساخت درخواست پرداخت برای سفارش.

    POST /api/payments/create/

    Body:
    {
        "order_id": 12
    }
    """

    permission_classes = [
        IsAuthenticated,
    ]

    serializer_class = (
        CreatePaymentSerializer
    )

    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        input_serializer = (
            self.get_serializer(
                data=request.data,
            )
        )

        input_serializer.is_valid(
            raise_exception=True,
        )

        order_id = (
            input_serializer
            .validated_data["order_id"]
        )

        order = get_object_or_404(
            Order,
            id=order_id,
            user=request.user,
        )

        callback_url = (
            getattr(
                settings,
                "PAYMENT_CALLBACK_URL",
                (
                    "http://localhost:5173/"
                    "payment/verify"
                ),
            )
        )

        try:
            result = PaymentCreateService(
                order=order,
                callback_url=callback_url,
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

        return Response(
            {
                "message": (
                    "درخواست پرداخت "
                    "با موفقیت ایجاد شد."
                ),
                "payment_url":
                    result.payment_url,
                "payment":
                    PaymentSerializer(
                        result.payment,
                        context={
                            "request": request,
                        },
                    ).data,
            },
            status=status.HTTP_201_CREATED,
        )
