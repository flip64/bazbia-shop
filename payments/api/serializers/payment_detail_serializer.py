from rest_framework import serializers

from payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """
    نمایش اطلاعات یک تراکنش پرداخت.
    """

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    payment_method_display = serializers.CharField(
        source="get_payment_method_display",
        read_only=True,
    )

    is_successful = serializers.BooleanField(
        read_only=True,
    )

    class Meta:
        model = Payment

        fields = [
            "id",
            "order",
            "amount",
            "payment_method",
            "payment_method_display",
            "status",
            "status_display",
            "gateway",
            "authority",
            "tracking_code",
            "reference_id",
            "error_message",
            "paid_at",
            "created_at",
            "updated_at",
            "is_successful",
        ]

        read_only_fields = fields
