from rest_framework import serializers
from django.db.models import Sum, Min, Max
from products.models import (
    Product, ProductImage, ProductVariant, Category, ProductSpecification,
    SpecialProduct, Tag, Attribute, AttributeValue, ProductVideo
)

# ==============================
# Product Image
# ==============================
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image', 'source_url', 'alt_text', 'is_main']

# ==============================
# Attribute Value
# ==============================
class AttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)

    class Meta:
        model = AttributeValue
        fields = ['id', 'attribute_name', 'value']

# ==============================
# Product Variant
# ==============================
class ProductVariantSerializer(serializers.ModelSerializer):
    attributes = AttributeValueSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'sku', 'price', 'discount_price', 'stock',
            'low_stock_threshold', 'expiration_date', 'attributes'
        ]

# ==============================
# Product
# ==============================
class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    category = serializers.SerializerMethodField()
    thumb = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    max_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description',
            'category', 'images', 'thumb', 'created_at',
            'quantity', 'min_price', 'max_price', 'data'
        ]

    def get_category(self, obj):
        return obj.category.name if obj.category else None

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
        total = obj.variants.aggregate(total=Sum('stock'))['total']
        return int(total or 0)

    def get_min_price(self, obj):
        min_discount = obj.variants.filter(discount_price__isnull=False).aggregate(
            min_price=Min('discount_price')
        )['min_price']
        if min_discount is not None:
            return min_discount
        return obj.variants.aggregate(min_price=Min('price'))['min_price'] or 0

    def get_max_price(self, obj):
        return obj.variants.aggregate(max_price=Max('price'))['max_price'] or 0

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        variants = ProductVariantSerializer(
            instance.variants.all(), many=True, context=self.context
        ).data
        rep['data'] = variants[0] if len(variants) == 1 else variants
        return rep

# ==============================
# Category
# ==============================
class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    parent_id = serializers.IntegerField(source='parent.id', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image', 'parent_id', 'subcategories']

    def get_subcategories(self, obj):
        return CategorySerializer(obj.subcategories.all(), many=True).data

# ==============================
# Special Product
# ==============================
class SpecialProductSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='product.name')
    slug = serializers.SlugField(source='product.slug')
    category = serializers.StringRelatedField(source='product.category')
    created_at = serializers.DateTimeField(source='product.created_at')
    thumb = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    max_price = serializers.SerializerMethodField()

    class Meta:
        model = SpecialProduct
        fields = [
            'id', 'name', 'slug', 'category', 'thumb', 'created_at',
            'quantity', 'min_price', 'max_price'
        ]

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
        total = obj.product.variants.aggregate(total=Sum('stock'))['total']
        return int(total or 0)

    def get_min_price(self, obj):
        min_discount = obj.product.variants.filter(discount_price__isnull=False).aggregate(
            min_price=Min('discount_price')
        )['min_price']
        if min_discount is not None:
            return min_discount
        return obj.product.variants.aggregate(min_price=Min('price'))['min_price'] or 0

    def get_max_price(self, obj):
        return obj.product.variants.aggregate(max_price=Max('price'))['max_price'] or 0

# ==============================
# Tag
# ==============================
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name']

# ==============================
# Product Specification
# ==============================
class ProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = ['name', 'value']

# ==============================
# Product Video
# ==============================
class ProductVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVideo
        fields = ['video', 'caption']

# ==============================
# Product Detail
# ==============================
class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = serializers.SerializerMethodField()
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    videos = ProductVideoSerializer(many=True, read_only=True)
    is_special = serializers.SerializerMethodField()
    special_details = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    max_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'category', 'tags',
            'specifications', 'images', 'videos', 'is_active', 'created_at',
            'updated_at', 'is_special', 'special_details', 'quantity',
            'min_price', 'max_price', 'data'
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

    def get_min_price(self, obj):
        min_discount = obj.variants.filter(discount_price__isnull=False).aggregate(
            min_price=Min('discount_price')
        )['min_price']
        if min_discount is not None:
            return min_discount
        return obj.variants.aggregate(min_price=Min('price'))['min_price'] or 0

    def get_max_price(self, obj):
        return obj.variants.aggregate(max_price=Max('price'))['max_price'] or 0

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        variants = ProductVariantSerializer(
            instance.variants.all(), many=True, context=self.context
        ).data
        rep['data'] = variants[0] if len(variants) == 1 else variants
        return rep
