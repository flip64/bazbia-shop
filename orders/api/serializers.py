class OrderSerializer(serializers.ModelSerializer):
    """
    نمایش کامل سفارش به همراه آیتم‌ها،
    آدرس، ارسال، کد رهگیری و اطلاعات پرداخت.
    """

    items = OrderItemSerializer(
        many=True,
        read_only=True,
    )

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    payment_method_display = serializers.CharField(
        source="get_payment_method_display",
        read_only=True,
    )

    # نام خروجی API برای هماهنگی با Vue
    tracking_code = serializers.CharField(
        source="shipping_tracking_code",
        read_only=True,
    )

    class Meta:
        model = Order

        fields = [
            "id",
            "user",

            "status",
            "status_display",

            "payment_method",
            "payment_method_display",

            "shipping_address",
            "shipping_address_snapshot",

            "shipping_method_code",
            "shipping_method_title",
            "shipping_quote_id",

            "tracking_code",
            "shipped_at",

            "items_total",
            "shipping_cost",
            "discount_amount",
            "total_price",

            "created_at",
            "updated_at",

            "items",
        ]

        read_only_fields = fields
