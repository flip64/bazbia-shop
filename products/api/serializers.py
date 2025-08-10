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
    name = serializers.CharField(source='product.name')
    slug = serializers.SlugField(source='product.slug')
    description = serializers.CharField(source='product.description')
    base_price = serializers.DecimalField(source='product.base_price', max_digits=10, decimal_places=0)
    category = serializers.StringRelatedField(source='product.category')
    images = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source='product.created_at')
    thumb = serializers.SerializerMethodField()

    class Meta:
        model = SpecialProduct
        fields = [
            'id', 'name', 'slug', 'description', 'base_price',
            'category', 'images', 'variants', 'thumb', 'created_at',
            'start_date', 'end_date', 'is_active'
        ]

    def get_thumb(self, obj):
        main_image = obj.product.images.filter(is_main=True).first()
        if main_image:
            return main_image.image.url
        first_image = obj.product.images.first()
        if first_image:
            return first_image.image.url
        return '/media/default-thumb.jpg'

    def get_images(self, obj):
        return [img.image.url for img in obj.product.images.all()]

    def get_variants(self, obj):
        return ProductVariantSerializer(obj.product.variants.all(), many=True).data
