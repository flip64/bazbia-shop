from rest_framework import serializers
from scrap_abdisite.models import WatchedURL, PriceHistory
from products.api.serializers import ProductVariantSerializer


# ==============================
# Serializer کامل برای PriceHistory
# ==============================
class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = ["id", "price", "checked_at"]


# ==============================
# Serializer کامل برای WatchedURL
# ==============================
class WatchedURLSerializer(serializers.ModelSerializer):
    # اطلاعات واریانت محصول
    variant = ProductVariantSerializer(read_only=True)
    # اطلاعات محصول از property
    product_name = serializers.CharField(source="variant.product.name", read_only=True)
    # تاریخچه قیمت‌ها
    history = PriceHistorySerializer(many=True, read_only=True)

    class Meta:
        model = WatchedURL
        fields = [
            "id",
            "user",
            "variant",
            "product_name",
            "url",
            "price",
            "created_at",
            "last_checked",
            "history",
        ]
        read_only_fields = ["product_name", "history"]
