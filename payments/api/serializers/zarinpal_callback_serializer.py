from rest_framework import serializers


class ZarinpalCallbackSerializer(
    serializers.Serializer
):
    """
    اطلاعات بازگشتی زرین‌پال که فرانت برای بک‌اند می‌فرستد.
    """

    authority = serializers.CharField(
        max_length=100,
        required=True,
        allow_blank=False,
        trim_whitespace=True,
    )

    status = serializers.ChoiceField(
        choices=[
            "OK",
            "NOK",
        ],
        required=True,
    )
