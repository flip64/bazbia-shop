from rest_framework import serializers
from scrap_abdisite.models import WatchedURL, PriceHistory
from products.api.serializers import ProductVariantSerializer



# ==============================
# Serializer کامل برای WatchedURL
# ==============================
class WatchedURLSerializer(serializers.ModelSerializer):
    # اطلاعات واریانت محصول
    variant = ProductVariantSerializer(read_only=True)
    # نام محصول با استفاده از property مدل
    product_name = serializers.SerializerMethodField()
    # تاریخچه قیمت‌ها
    
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
            
        ]
        read_only_fields = ["product_name", "history"]

    # متد برای نام محصول
    def get_product_name(self, obj):
        product = getattr(obj, 'product', None)
        if product:
            return product.name
        return "بدون محصول"
