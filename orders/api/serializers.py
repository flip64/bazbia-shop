from rest_framework import serializers
from orders.models import Order, OrderItem, Cart, CartItem, SalesSummary


# ==============================
# 🎯 سریالایزر آیتم سبد خرید
# ==============================




class CartItemSerializer(serializers.ModelSerializer):
    """
    اطلاعات کامل یک آیتم سبد خرید برای فرانت‌اند.
    """

    product_name = serializers.CharField(
        source="variant.product.name",
        read_only=True,
    )

    product_slug = serializers.CharField(
        source="variant.product.slug",
        read_only=True,
    )

    variant_name = serializers.CharField(
        source="variant.__str__",
        read_only=True,
    )

    variant_stock = serializers.IntegerField(
        source="variant.stock",
        read_only=True,
    )

    price = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",

            # شناسه واریانت
            "variant",

            # اطلاعات محصول
            "product_name",
            "product_slug",

            # اطلاعات واریانت
            "variant_name",
            "variant_stock",

            # اطلاعات خرید
            "quantity",
            "price",
            "total_price",

            # تصویر
            "image",
        ]

    def get_price(self, obj):
        """
        قیمت نهایی یک عدد کالا.

        در صورت وجود تخفیف، قیمت تخفیف‌خورده استفاده می‌شود.
        """
        variant = obj.variant

        if variant.discount_price is not None:
            return variant.discount_price

        return variant.price

    def get_total_price(self, obj):
        """
        قیمت کل این ردیف سبد خرید.
        """
        return self.get_price(obj) * obj.quantity

    def get_image(self, obj):
        """
        اول تصویر اصلی واریانت، سپس تصویر اصلی محصول
        و در نهایت اولین تصویر محصول را برمی‌گرداند.
        """
        request = self.context.get("request")

        variant = obj.variant
        product = variant.product

        main_image = (
            variant.images.filter(
                is_main=True,
            ).first()
            or product.images.filter(
                is_main=True,
            ).first()
            or product.images.first()
        )

        if not main_image or not main_image.image:
            return None

        image_url = main_image.image.url

        if request:
            return request.build_absolute_uri(
                image_url,
            )

        return image_url


# ==============================
# سبد خرید
# ==============================
class CartSerializer(serializers.ModelSerializer):
    """
    نمایش کامل سبد خرید به همراه آیتم‌ها.
    """

    items = CartItemSerializer(
        many=True,
        read_only=True,
    )

    total_price = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id",
            "user",
            "session_key",
            "items",
            "total_price",
            "total_items",
        ]

    def get_total_price(self, obj):
        return obj.total_price()

    def get_total_items(self, obj):
        return sum(
            item.quantity
            for item in obj.items.all()
        )


# ==============================
# ورودی افزودن به سبد
# ==============================
class CartItemCreateSerializer(serializers.Serializer):
    """
    اطلاعات لازم برای افزودن یک واریانت به سبد.
    """

    variant_id = serializers.IntegerField(
        required=True,
        min_value=1,
    )

    quantity = serializers.IntegerField(
        required=False,
        default=1,
        min_value=1,
    )


# ==============================
# ورودی تغییر تعداد
# ==============================
class CartItemUpdateSerializer(serializers.Serializer):
    """
    اطلاعات لازم برای تغییر تعداد یک آیتم موجود.
    """

    quantity = serializers.IntegerField(
        required=True,
        min_value=1,
    )




# ==============================
# 🎯 سریالایزر آیتم سفارش
# ==============================
class OrderItemSerializer(serializers.ModelSerializer):
    """
    نمایش آیتم‌های داخل سفارش
    """
    variant_name = serializers.CharField(source='variant.__str__', read_only=True)
    product_name = serializers.CharField(source='variant.product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'variant',
            'variant_name',
            'product_name',
            'quantity',
            'price',
        ]


# ==============================
# 🎯 سریالایزر سفارش
# ==============================
class OrderSerializer(serializers.ModelSerializer):
    """
    نمایش سفارش به همراه آیتم‌هایش
    """
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'user',
            'status',
            'status_display',
            'total_price',
            'created_at',
            'updated_at',
            'items',
        ]


# ==============================
# 🎯 سریالایزر خلاصه فروش (SalesSummary)
# ==============================
class SalesSummarySerializer(serializers.ModelSerializer):
    """
    نمایش داده‌های آماری خلاصه فروش محصولات
    """
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_name = serializers.CharField(source='variant.__str__', read_only=True)

    class Meta:
        model = SalesSummary
        fields = [
            'id',
            'product_name',
            'variant_name',
            'total_quantity',
            'total_amount',
            'period_start',
            'period_end',
        ]

