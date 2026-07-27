from rest_framework import serializers


class ExternalPackingItemSerializer(serializers.Serializer):
    """
    مشخصات یک کالا برای مشتریان خارجی API.
    """

    name = serializers.CharField(
        max_length=255,
    )

    length = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
    )

    width = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
    )

    height = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
    )

    weight = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01,
    )

    quantity = serializers.IntegerField(
        min_value=1,
        default=1,
    )

    fragile = serializers.BooleanField(
        required=False,
        default=False,
    )

    can_rotate = serializers.BooleanField(
        required=False,
        default=True,
    )


class ExternalPackingRequestSerializer(
    serializers.Serializer
):
    """
    ورودی endpoint عمومی موتور بسته‌بندی.
    """

    items = ExternalPackingItemSerializer(
        many=True,
        allow_empty=False,
    )


class CartShippingQuoteRequestSerializer(
    serializers.Serializer
):
    """
    ورودی محاسبه ارسال سبد فروشگاه بازبیا.

    فرانت فقط شناسه آدرس را ارسال می‌کند.
    """

    address_id = serializers.IntegerField(
        min_value=1,
    )
