from rest_framework import serializers
from scrap_abdisite.models import WatchedURL, PriceHistory
from products.models import ProductVariant, Product
from suppliers.models import Supplier


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "slug"]


class ProductVariantSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = ProductVariant
        fields = ["id", "name", "price", "product"]


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "name"]


class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = ["id", "price", "checked_at"]


class WatchedURLSerializer(serializers.ModelSerializer):
    variant = ProductVariantSerializer(read_only=True)
    supplier = SupplierSerializer(read_only=True)
    history = PriceHistorySerializer(many=True, read_only=True)
    user = serializers.StringRelatedField()

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
