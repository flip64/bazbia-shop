from rest_framework import serializers
from products.models import Product ,ProductImage,ProductVariant
from products.models import Category  # مدل دسته‌بندی شما



class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_main']


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['sku', 'price', 'discount_price', 'stock', 'attributes']


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'base_price', 'category', 'images', 'variants', 'created_at']


class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image', 'parent_id', 'subcategories']

    def get_subcategories(self, obj):
        return CategorySerializer(obj.subcategories.all(), many=True).data

    parent_id = serializers.IntegerField(source='parent.id', read_only=True)



class SpecialProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer()  # nested serializer

    class Meta:
        model = SpecialProduct
        fields = ['id', 'product', 'title', 'start_date', 'end_date', 'is_active']
