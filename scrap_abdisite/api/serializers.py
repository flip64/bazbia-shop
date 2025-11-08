from rest_framework import serializers
from scrap_abdisite.models import WatchedURL, PriceHistory
from products.models import ProductVariant, Product
from suppliers.models import Supplier


class ProductSerializer(serializers.ModelSerializer):
    """سریالایزر محصول پایه"""
    class Meta:
        model = Product
        fields = ["id", "name", "slug"]


class ProductVariantSerializer(serializers.ModelSerializer):
    """سریالایزر واریانت محصول، شامل نام محصول"""
    product = ProductSerializer(read_only=True)

    class Meta:
        model = ProductVariant
        fields = ["id", "name", "price", "product"]


class SupplierSerializer(serializers.ModelSerializer):
    """سریالایزر تأمین‌کننده"""
    class Meta:
        model = Supplier
        fields = ["id", "name", "website", "contact_info"]
        extra_kwargs = {
            "website": {"required": False},
            "contact_info": {"required": False},
        }


class PriceHistorySerializer(serializers.ModelSerializer):
    """سریالایزر تاریخچه قیمت"""
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    checked_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = PriceHistory
        fields = ["id", "price", "checked_at"]


class WatchedURLSerializer(serializers.ModelSerializer):
    """سریالایزر کامل WatchedURL با تمام جزئیات"""
    variant = ProductVariantSerializer(read_only=True)
    supplier = SupplierSerializer(read_only=True)
    history = PriceHistorySerializer(many=True, read_only=True)
    user = serializers.StringRelatedField()
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    last_checked = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, allow_null=True)

    class Meta:
        model = WatchedURL
        fields = [
            "id",
            "user",
            "variant",
            "supplier",
            "url",
            "price",
            "created_at",
            "last_checked",
            "history",
        ]
        read_only_fields = ["id", "created_at", "last_checked"]
