# products/api/serializers.py
from rest_framework import serializers
from django.db.models import Sum
from products.models import Product, ProductImage, ProductVariant, Tag, ProductSpecification, ProductVideo

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image', 'source_url', 'alt_text', 'is_main']

class ProductVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVideo
        fields = ['video', 'caption']

class ProductVariantSerializer(serializers.ModelSerializer):
    attributes = serializers.SerializerMethodField()
    thumb = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ['id', 'sku', 'price', 'discount_price', 'stock', 'attributes', 'thumb']

    def get_attributes(self, obj):
        return [f"{attr.attribute.name}: {attr.value}" for attr in obj.attributes.all()]

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
    category = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    specifications = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True, read_only=True)
    videos = ProductVideoSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    quantity = serializers.SerializerMethodField()
    product_link = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description',
            'price', 'quantity', 'category', 'tags',
            'specifications', 'images', 'videos',
            'variants', 'product_link'
        ]

    def get_category(self, obj):
        return obj.category.slug if obj.category else None

    def get_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]

    def get_specifications(self, obj):
        return [f"{spec.name}: {spec.value}" for spec in obj.specifications.all()]

    def get_quantity(self, obj):
        total = obj.variants.aggregate(total=Sum('stock'))['total']
        return int(total or 0)

    def get_product_link(self, obj):
        request = self.context.get('request')
        url = f"/products/{obj.slug}/"
        if request:
            return request.build_absolute_uri(url)
        return url
