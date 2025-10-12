from rest_framework import serializers
from orders.models import Order, OrderItem, Cart, CartItem, SalesSummary


# ==============================
# 🎯 سریالایزر آیتم سبد خرید
# ==============================
class CartItemSerializer(serializers.ModelSerializer):
    """
    نمایش و مدیریت آیتم‌های سبد خرید
    """
    variant_name = serializers.CharField(source='variant.__str__', read_only=True)
    price = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id',
            'variant',
            'variant_name',
            'quantity',
            'price',
            'total_price',
            'image',
        ]

    def get_price(self, obj):
        return obj.variant.discount_price or obj.variant.price

    def get_total_price(self, obj):
        return (obj.variant.discount_price or obj.variant.price) * obj.quantity

    def get_image(self, obj):
        """برگرداندن آدرس تصویر اصلی واریانت یا محصول"""
        request = self.context.get('request')
        variant = obj.variant
        product = variant.product

        main_image = (
            variant.images.filter(is_main=True).first() or
            product.images.filter(is_main=True).first() or
            product.images.first()
        )

        if main_image and main_image.image:
            image_url = main_image.image.url
            return request.build_absolute_uri(image_url) if request else image_url
        return None


# ==============================
# 🎯 سریالایزر سبد خرید
# ==============================
class CartSerializer(serializers.ModelSerializer):
    """
    نمایش کامل سبد خرید به همراه آیتم‌ها
    """
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            'id',
            'user',
            'session_key',
            'items',
            'total_price',
            'total_items',
        ]

    def get_total_price(self, obj):
        return obj.total_price()

    def get_total_items(self, obj):
        return sum(item.quantity for item in obj.items.all())


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


# ==============================
# 🎯 سریالایزر ورودی برای افزودن/ویرایش آیتم سبد
# ==============================
class CartItemInputSerializer(serializers.Serializer):
    """
    سریالایزر ساده برای افزودن یا بروزرسانی آیتم در سبد خرید
    """
    variant_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(min_value=1, default=1)
