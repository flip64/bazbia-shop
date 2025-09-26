
from rest_framework import serializers
from django.db.models import Sum
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
    quantity = serializers.SerializerMethodField()  # <-- اضافه شد

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'base_price',
            'category', 'images', 'variants', 'thumb', 'created_at', 'quantity'
        ]

    def get_category(self, obj):
        if obj.category:
            return [obj.category.name]
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

    def get_quantity(self, obj):
        # جمعِ stock از واریانت‌ها در سطح دیتابیس برای کارایی بهتر
        total = obj.variants.aggregate(total=Sum('stock'))['total']
        return int(total or 0)


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
    quantity = serializers.SerializerMethodField()  # <-- اضافه شد

    class Meta:
        model = SpecialProduct
        fields = ['id', 'name', 'slug', 'base_price', 'category', 'thumb', 'created_at', 'quantity']

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

    def get_quantity(self, obj):
        # special -> product -> variants
        total = obj.product.variants.aggregate(total=Sum('stock'))['total']
        return int(total or 0)


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


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'sku', 'price', 'discount_price', 'stock']


class ProductListSerializer(serializers.ModelSerializer):
    variants = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    discount_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug',
            'price', 'discount_price',  # 👈 اضافه شد
            'category', 'variants',
            'created_at'
        ]

    def get_category(self, obj):
        return obj.category.name if obj.category else None

    def get_price(self, obj):
        """کمترین قیمت از بین واریانت‌ها"""
        variant = obj.variants.order_by('price').first()
        return int(variant.price) if variant and variant.price else None

    def get_discount_price(self, obj):
        """کمترین قیمت تخفیف‌خورده از بین واریانت‌ها"""
        variant = obj.variants.exclude(discount_price__isnull=True).order_by('discount_price').first()
        return int(variant.discount_price) if variant and variant.discount_price else None

    def get_variants(self, obj):
        variants = obj.variants.all()
        if not variants.exists():
            return None  

        serializer = ProductVariantSerializer(variants, many=True)
        if variants.count() == 1:
            return serializer.data[0]  # 👈 یک واریانت → object
        return serializer.data



class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = serializers.SerializerMethodField()
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    videos = ProductVideoSerializer(many=True, read_only=True)
    is_special = serializers.SerializerMethodField()
    special_details = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()  # <-- اضافه شد

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'base_price',
            'category', 'tags', 'specifications', 'variants',
            'images', 'videos', 'is_active', 'created_at', 'updated_at',
            'is_special', 'special_details', 'quantity'
        ]

    def get_is_special(self, obj):
        special = getattr(obj, 'special', None)
        return bool(special and getattr(special, 'is_active', False))

    def get_special_details(self, obj):
        special = getattr(obj, 'special', None)
        if special:
            return {
                'title': special.title,
                'start_date': special.start_date,
                'end_date': special.end_date
            }
        return None

    def get_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]

    def get_quantity(self, obj):
        total = obj.variants.aggregate(total=Sum('stock'))['total']
        return int(total or 0)
