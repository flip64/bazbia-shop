from rest_framework import serializers
from products.models import (
    Product, ProductImage, ProductVariant, Category, ProductSpecification,
    SpecialProduct, Tag, Attribute, AttributeValue, ProductVideo
)


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image', 'source_url', 'alt_text', 'is_main']


class AttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)

    class Meta:
        model = AttributeValue
        fields = ['id', 'attribute_name', 'value']


class ProductVariantSerializer(serializers.ModelSerializer):
    attributes = AttributeValueSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'sku', 'price', 'discount_price', 'stock',
            'low_stock_threshold', 'expiration_date', 'attributes'
        ]


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    category = serializers.SerializerMethodField()
    thumb = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'base_price',
            'category', 'images', 'variants', 'thumb', 'created_at'
        ]

    def get_category(self, obj):
        if obj.category:
            return [obj.category.name]  # برگرداندن دسته‌بندی در قالب لیست
        return []

    def get_thumb(self, obj):
        request = self.context.get('request')
        main_image = obj.images.filter(is_main=True).first()
        if main_image:
            url = main_image.image.url
        elif obj.images.exists():
            url = obj.images.first().image.url
        else:
            url = '/media/default-thumb.jpg'

        if request:
            return request.build_absolute_uri(url)
        return url


class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    parent_id = serializers.IntegerField(source='parent.id', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image', 'parent_id', 'subcategories']

    def get_subcategories(self, obj):
        return CategorySerializer(obj.subcategories.all(), many=True).data


class SpecialProductSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='product.name')
    slug = serializers.SlugField(source='product.slug')
    base_price = serializers.DecimalField(source='product.base_price', max_digits=10, decimal_places=0)
    category = serializers.StringRelatedField(source='product.category')
    created_at = serializers.DateTimeField(source='product.created_at')
    thumb = serializers.SerializerMethodField()

    class Meta:
        model = SpecialProduct
        fields = ['id', 'name', 'slug', 'base_price', 'category', 'thumb', 'created_at']

    def get_thumb(self, obj):
     request = self.context.get('request')
     main_image = obj.product.images.filter(is_main=True).first()
     if main_image:
        url = main_image.image.url
     elif obj.product.images.exists():
        url = obj.product.images.first().image.url
     else:
        url = '/media/default-thumb.jpg'

     if request:
        return request.build_absolute_uri(url)
     return url




    def get_images(self, obj):
        return [img.image.url for img in obj.product.images.all()]

    def get_variants(self, obj):
        return ProductVariantSerializer(obj.product.variants.all(), many=True).data


class NewProductSerializer(serializers.ModelSerializer):
    
    name = serializers.CharField(source='product.name')
    slug = serializers.SlugField(source='product.slug')
    base_price = serializers.DecimalField(source='product.base_price', max_digits=10, decimal_places=0)
    category = serializers.StringRelatedField(source='product.category')
    created_at = serializers.DateTimeField(source='product.created_at')
    thumb = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'base_price', 'category', 'thumb', 'created_at']

    def get_thumb(self, obj):
        request = self.context.get('request')
        main_image = obj.images.filter(is_main=True).first()
        if main_image:
            url = main_image.image.url
        elif obj.images.exists():
            url = obj.images.first().image.url
        else:
            url = '/media/default-thumb.jpg'

        if request:
            return request.build_absolute_uri(url)
        return url


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name']


class ProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = ['name', 'value']


class ProductVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVideo
        fields = ['video', 'caption']


class ProductListSerializer(serializers.ModelSerializer):
    thumb = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'base_price', 'category', 'thumb', 'created_at']

    def get_thumb(self, obj):
        request = self.context.get('request')
        main_image = obj.images.filter(is_main=True).first()
        if main_image:
            url = main_image.image.url
        elif obj.images.exists():
            url = obj.images.first().image.url
        else:
            url = '/media/default-thumb.jpg'

        if request:
            return request.build_absolute_uri(url)
        return url

class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = serializers.SerializerMethodField()
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    videos = ProductVideoSerializer(many=True, read_only=True)
    is_special = serializers.SerializerMethodField()
    special_details = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'base_price',
            'category', 'tags', 'specifications', 'variants',
            'images', 'videos', 'is_active', 'created_at', 'updated_at',
            'is_special', 'special_details'
        ]

    def get_is_special(self, obj):
        return hasattr(obj, 'special') and obj.special.is_active

    def get_special_details(self, obj):
        if hasattr(obj, 'special'):
            return {
                'title': obj.special.title,
                'start_date': obj.special.start_date,
                'end_date': obj.special.end_date
            }
        return None

    def get_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]
