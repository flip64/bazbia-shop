from decimal import Decimal

from rest_framework import serializers


class ExternalPackingItemSerializer(serializers.Serializer):
    """
    مشخصات فیزیکی یک کالا برای API عمومی بسته‌بندی.

    واحدها:
    - length_cm: سانتی‌متر
    - width_cm: سانتی‌متر
    - height_cm: سانتی‌متر
    - weight_grams: گرم
    - quantity: تعداد کالا
    """

    name = serializers.CharField(
        max_length=255,
    )

    length_cm = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        help_text="طول کالا بر حسب سانتی‌متر",
    )

    width_cm = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        help_text="عرض کالا بر حسب سانتی‌متر",
    )

    height_cm = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        help_text="ارتفاع کالا بر حسب سانتی‌متر",
    )

    weight_grams = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
        help_text="وزن یک واحد کالا بر حسب گرم",
    )

    quantity = serializers.IntegerField(
        min_value=1,
        default=1,
        help_text="تعداد کالا",
    )

    fragile = serializers.BooleanField(
        required=False,
        default=False,
        help_text="آیا کالا شکستنی است؟",
    )

    can_rotate = serializers.BooleanField(
        required=False,
        default=True,
        help_text="آیا کالا هنگام بسته‌بندی قابلیت چرخش دارد؟",
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
    ورودی محاسبه هزینه ارسال سبد فروشگاه بازبیا.

    فرانت فقط شناسه آدرس متعلق به کاربر را ارسال می‌کند.
    """

    address_id = serializers.IntegerField(
        min_value=1,
        help_text="شناسه آدرس تحویل مشتری",
    )
