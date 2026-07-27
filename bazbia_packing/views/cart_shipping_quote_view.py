from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from customers.models import CustomerAddress
from orders.models import Cart

from bazbia_packing.api.serializers import (
    CartShippingQuoteRequestSerializer,
)
from bazbia_packing.services.fixed_shipping_quote_service import (
    FixedShippingQuoteService,
)


class CartShippingQuoteAPIView(APIView):
    """
    API داخلی محاسبه هزینه ارسال Checkout بازبیا.

    فرانت فقط address_id را ارسال می‌کند.
    سبد و آدرس از دیتابیس خوانده می‌شوند.

    فعلاً یک نرخ ثابت برای تمام سفارش‌ها برمی‌گرداند.
    """

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(self, request):
        serializer = CartShippingQuoteRequestSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        address_id = serializer.validated_data[
            "address_id"
        ]

        customer = getattr(
            request.user,
            "customer_profile",
            None,
        )

        if customer is None:
            return Response(
                {
                    "detail": (
                        "برای این کاربر پروفایل "
                        "مشتری وجود ندارد."
                    ),
                    "code": "customer_profile_not_found",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            address = CustomerAddress.objects.get(
                id=address_id,
                customer=customer,
            )
        except CustomerAddress.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "آدرس انتخاب‌شده وجود ندارد "
                        "یا متعلق به این کاربر نیست."
                    ),
                    "code": "address_not_found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            cart = Cart.objects.get(
                user=request.user,
                is_active=True,
            )
        except Cart.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "سبد خرید فعال پیدا نشد."
                    ),
                    "code": "active_cart_not_found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not cart.items.exists():
            return Response(
                {
                    "detail": "سبد خرید خالی است.",
                    "code": "empty_cart",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        quote_service = FixedShippingQuoteService(
            cart=cart,
            address=address,
        )

        quote = quote_service.calculate()

        return Response(
            quote,
            status=status.HTTP_200_OK,
        )
