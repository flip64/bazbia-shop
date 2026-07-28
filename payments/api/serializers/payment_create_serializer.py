from rest_framework import serializers


class CreatePaymentSerializer(serializers.Serializer):
    """
    داده ورودی برای ساخت درخواست پرداخت.

    مبلغ از فرانت دریافت نمی‌شود و مستقیماً از سفارش
    خوانده خواهد شد.
    """

    order_id = serializers.IntegerField(
        min_value=1,
        required=True,
        help_text="شناسه سفارش متعلق به کاربر",
    )
