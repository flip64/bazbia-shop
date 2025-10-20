from rest_framework import serializers
from django.db.models import Sum
from products.models import (
    Product, ProductImage, ProductVariant, Category,
    ProductSpecification, SpecialProduct, Tag,
    Attribute, AttributeValue, ProductVideo
)

# ------------------------------
# 🔹 تصاویر محصول
# ------------------------------
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image', 'source_url', 'alt_text', 'is_main']


# ------------------------------
# 🔹 مقادیر ویژگی‌ها
# ------------------------------
class AttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)

    class Meta:
        model = AttributeValue
        fields = ['id', 'attribute_name', 'value']


# ------------------------------
# 🔹 واریانت‌های محصول
# ------------------------------
class ProductVariantSerializer(serializers.ModelSerializer):
    attributes = AttributeValueSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'sku', 'price', 'discount_price', 'stock',
            'low_stock_threshold', 'expiration_date', 'attributes'
        ]


# ------------------------------
# 🔹 سریالایزر اصلی محصول
# ------------------------------
class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    category = serializers.SerializerMethodField()
    thumb = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()

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
        total = obj.variants.aggregate(total=Sum('stock'))['total']
        return int(total or 0)


# ------------------------------
# 🔹 دسته‌بندی‌ها
# ------------------------------
class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    parent_id = serializers.IntegerField(source='parent.id', read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image', 'parent_id', 'subcategories']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        elif obj.image:
            from django.conf import settings
            return f"{settings.BASE_URL}{obj.image.url}"
        return None

    def get_subcategories(self, obj):
        return CategorySerializer(obj.subcategories.all(), many=True, context=self.context).data


# ------------------------------
# 🔹 محصولات ویژه
# ------------------------------
class SpecialProductSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='product.name')
    slug = serializers.SlugField(source='product.slug')
    base_price = serializers.DecimalField(source='product.base_price', max_digits=10, decimal_places=0)
    category = serializers.StringRelatedField(source='product.category')
    created_at = serializers.DateTimeField(source='product.created_at')
    thumb = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()

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
        total = obj.product.variants.aggregate(total=Sum('stock'))['total']
        return int(total or 0)


# ------------------------------
# 🔹 تگ‌ها و مشخصات
# ------------------------------
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


# ------------------------------
# 🔹 لیست محصولات برای صفحه فروشگاه
# ------------------------------
class ProductListSerializer(serializers.ModelSerializer):
    variants = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    discount_price = serializers.SerializerMethodField()
    thumb = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug',
            'price', 'discount_price',
            'category', 'thumb', 'variants',
            'created_at'
        ]

    def get_category(self, obj):
        return obj.category.name if obj.category else None

    def get_thumb(self, obj):
        main_image = obj.images.filter(is_main=True).first()
        if main_image:
            url = main_image.image.url
        elif obj.images.exists():
            url = obj.images.first().image.url
        else:
            url = '/media/default-thumb.jpg'

        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(url)
        return url

    def get_price(self, obj):
        variant = obj.variants.order_by('price').first()
        return int(variant.price) if variant and variant.price else None

    def get_discount_price(self, obj):
        variant = obj.variants.exclude(discount_price__isnull=True).order_by('discount_price').first()
        return int(variant.discount_price) if variant and variant.discount_price else None

    def get_variants(self, obj):
        variants = obj.variants.all()
        if not variants.exists():
            return None
        if variants.count() == 1:
            return None

        serialized = []
        for variant in variants:
            main_image = variant.images.filter(is_main=True).first()
            if main_image:
                url = main_image.image.url
            elif variant.images.exists():
                url = variant.images.first().image.url
            else:
                url = '/media/default-thumb.jpg'

            request = self.context.get('request')
            if request:
                url = request.build_absolute_uri(url)

            serialized.append({
                'id': variant.id,
                'sku': variant.sku,
                'price': int(variant.price) if variant.price else None,
                'discount_price': int(variant.discount_price) if variant.discount_price else None,
                'stock': variant.stock,
                'thumb': url,
                'attributes': [
                    f"{attr.attribute.name}: {attr.value}" for attr in variant.attributes.all()
                ]
            })
        return serialized


# ------------------------------
# 🔹 جزئیات کامل محصول
# ------------------------------
class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = serializers.SerializerMethodField()
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    videos = ProductVideoSerializer(many=True, read_only=True)
    is_special = serializers.SerializerMethodField()
    special_details = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()

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
