from rest_framework import serializers

from payments.models import Payment


class PaymentSerializer(
    serializers.ModelSerializer
):
    """
    نمایش اطلاعات کامل یک تراکنش پرداخت.
    """

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    payment_method_display = serializers.CharField(
        source="get_payment_method_display",
        read_only=True,
    )

    order_status = serializers.CharField(
        source="order.status",
        read_only=True,
    )

    is_successful = serializers.BooleanField(
        read_only=True,
    )

    can_retry = serializers.SerializerMethodField()

    class Meta:
        model = Payment

        fields = [
            "id",
            "order",
            "order_status",
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
            "can_retry",
        ]

        read_only_fields = fields

    def get_can_retry(
        self,
        obj: Payment,
    ) -> bool:
        """
        مشخص می‌کند امکان تلاش مجدد برای پرداخت وجود دارد یا نه.
        """

        retryable_statuses = {
            Payment.Status.PENDING,
            Payment.Status.FAILED,
            Payment.Status.CANCELLED,
        }

        return (
            obj.status in retryable_statuses
            and obj.order.status != "paid"
        )
