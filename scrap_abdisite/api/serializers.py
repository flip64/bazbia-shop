# -*- coding: utf-8 -*-
from rest_framework import serializers
from products.models import (
    Product, ProductVariant, Category, Tag,
    Attribute, AttributeValue, ProductImage,
    ProductVariantImage
)

# ==============================
# Serializer برای Category
# ==============================
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "image", "parent"]


# ==============================
# Serializer برای Tag
# ==============================
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


# ==============================
# Serializer برای Product (خلاصه)
# ==============================
class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "slug", "category", "tags"]


# ==============================
# Serializer برای AttributeValue
# ==============================
class AttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source="attribute.name", read_only=True)

    class Meta:
        model = AttributeValue
        fields = ["id", "attribute_name", "value"]


# ==============================
# Serializer برای تصاویر واریانت (ProductVariantImage)
# ==============================
class ProductVariantImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariantImage
        fields = ["id", "image", "source_url", "alt_text", "is_main"]


# ==============================
# Serializer برای واریانت محصول (ProductVariant)
# ==============================
class ProductVariantSerializer(serializers.ModelSerializer):
    # 🔹 نمایش نام محصول مرتبط
    product_name = serializers.CharField(source="product.name", read_only=True)
    # 🔹 نمایش slug محصول
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    # 🔹 ویژگی‌ها (مثل رنگ و سایز)
    attributes = AttributeValueSerializer(many=True, read_only=True)
    # 🔹 تصاویر واریانت
    images = ProductVariantImageSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            "id", "sku", "product", "product_name", "product_slug",
            "price", "discount_price", "stock", "low_stock_threshold",
            "attributes", "images", "purchase_price", "profit_percent",
            "calculated_price", "expiration_date", "created_at"
        ]
        read_only_fields = ["product_name", "product_slug", "calculated_price"]


# ==============================
# Serializer کامل برای محصول همراه با واریانت‌ها
# ==============================
class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "description", "base_price",
            "category", "tags", "is_active", "quantity",
            "created_at", "updated_at", "variants"
        ]
