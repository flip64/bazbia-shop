from rest_framework import serializers
from products.models import Product ,ProductImage,ProductVariant
from products.models import Category  # مدل دسته‌بندی شما
from products.models import SpecialProduct


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
    thumb = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'base_price',
            'category', 'images', 'variants', 'thumb', 'created_at'
        ]

    def get_thumb(self, obj):
        main_image = obj.images.filter(is_main=True).first()
        if main_image:
            return main_image.image.url
        first_image = obj.images.first()
        if first_image:
            return first_image.image.url
        return '/media/default-thumb.jpg'  # مسیر تصویر پیش‌فرض (اختیاری)


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
