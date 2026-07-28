from rest_framework import serializers


class VerifyPaymentSerializer(
    serializers.Serializer
):
    """
    داده ورودی برای تأیید پرداخت آزمایشی.
    """

    payment_id = serializers.IntegerField(
        min_value=1,
        required=True,
    )

    authority = serializers.CharField(
        max_length=100,
        required=True,
        allow_blank=False,
        trim_whitespace=True,
    )

    mock_status = serializers.ChoiceField(
        choices=[
            "success",
            "failed",
            "cancelled",
        ],
        default="success",
    )
