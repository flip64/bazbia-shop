# -*- coding: utf-8 -*-

from rest_framework import serializers

from products.models import (
    Product,
    ProductImage,
    ProductVariant,
    ProductVariantImage,
    Category,
    ProductSpecification,
    SpecialProduct,
    Tag,
    AttributeValue,
    ProductVideo,
)

from products.services.product_stock import (
    calculate_product_stock,
)
from products.services.variant_stock import (
    calculate_variant_available_stock,
)
# ------------------------------
# دسته‌بندی‌ها
# ------------------------------
class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    parent_id = serializers.IntegerField(
        source="parent.id",
        read_only=True,
    )

    image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "image",
            "parent_id",
            "product_count",
            "subcategories",
        ]

    def get_image(self, obj):
        request = self.context.get("request")

        if not obj.image:
            return None

        if request:
            return request.build_absolute_uri(
                obj.image.url
            )

        return obj.image.url

    def get_subcategories(self, obj):
        return CategorySerializer(
            obj.subcategories.all(),
            many=True,
            context=self.context,
        ).data



    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()

# ------------------------------
# تگ‌ها
# ------------------------------
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = [
            "name",
        ]


# ------------------------------
# مشخصات محصول
# ------------------------------
class ProductSpecificationSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = ProductSpecification
        fields = [
            "name",
            "value",
        ]


# ------------------------------
# ویدئوهای محصول
# ------------------------------
class ProductVideoSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = ProductVideo
        fields = [
            "video",
            "caption",
        ]



class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = [
            "image",
            "source_url",
            "alt_text",
            "is_main",
        ]


class ProductVariantImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariantImage
        fields = [
            "image",
            "source_url",
            "alt_text",
            "is_main",
        ]


class AttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(
        source="attribute.name",
        read_only=True,
    )

    class Meta:
        model = AttributeValue
        fields = [
            "id",
            "attribute_name",
            "value",
        ]


class ProductVariantSerializer(serializers.ModelSerializer):
    attributes = AttributeValueSerializer(
        many=True,
        read_only=True,
    )

    stock = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()
    images = ProductVariantImageSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "sku",
            "price",
            "discount_price",
            "final_price",
            "stock",
            "in_stock",
            "low_stock_threshold",
            "expiration_date",
            "label",
            "attributes",
            "images",
        ]

    @staticmethod
    def _available_stock(obj):
        cached_stock = getattr(
            obj,
            "_serializer_available_stock",
            None,
        )

        if cached_stock is None:
            cached_stock = int(
                calculate_variant_available_stock(obj)
            )
            obj._serializer_available_stock = cached_stock

        return cached_stock

    def get_stock(self, obj):
        """
        موجودی قابل عرضه واریانت را با همان نام stock
        برای فرانت‌اند ارسال می‌کند.
        """

        return self._available_stock(obj)

    def get_in_stock(self, obj):
        return self._available_stock(obj) > 0

    def get_final_price(self, obj):
        if (
            obj.discount_price is not None
            and obj.discount_price > 0
            and obj.discount_price < obj.price
        ):
            return int(obj.discount_price)

        return int(obj.price)

    def get_label(self, obj):
        attributes = obj.attributes.all()

        label = " / ".join(
            f"{attribute.attribute.name}: {attribute.value}"
            for attribute in attributes
        )

        return label or obj.sku

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(
        many=True,
        read_only=True,
    )

    variants = ProductVariantSerializer(
        many=True,
        read_only=True,
    )

    category = serializers.SerializerMethodField()
    thumb = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "base_price",
            "category",
            "images",
            "variants",
            "thumb",
            "created_at",
            "quantity",
        ]

    def get_category(self, obj):
        if obj.category:
            return [obj.category.name]

        return []

    def get_thumb(self, obj):
        request = self.context.get("request")

        main_image = obj.images.filter(
            is_main=True
        ).first()

        if main_image and main_image.image:
            url = main_image.image.url

        else:
            first_image = obj.images.first()

            if first_image and first_image.image:
                url = first_image.image.url
            else:
                url = "/media/default-thumb.jpg"

        if request:
            return request.build_absolute_uri(url)

        return url

    def get_quantity(self, obj):
        return calculate_product_stock(obj)


class SpecialProductSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        source="product.name",
    )

    slug = serializers.SlugField(
        source="product.slug",
    )

    base_price = serializers.DecimalField(
        source="product.base_price",
        max_digits=12,
        decimal_places=0,
    )

    category = serializers.StringRelatedField(
        source="product.category",
    )

    created_at = serializers.DateTimeField(
        source="product.created_at",
    )

    thumb = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()

    class Meta:
        model = SpecialProduct
        fields = [
            "id",
            "name",
            "slug",
            "base_price",
            "category",
            "thumb",
            "created_at",
            "quantity",
        ]

    def get_thumb(self, obj):
        request = self.context.get("request")

        main_image = obj.product.images.filter(
            is_main=True
        ).first()

        if main_image and main_image.image:
            url = main_image.image.url

        else:
            first_image = obj.product.images.first()

            if first_image and first_image.image:
                url = first_image.image.url
            else:
                url = "/media/default-thumb.jpg"

        if request:
            return request.build_absolute_uri(url)

        return url

    def get_quantity(self, obj):
        return calculate_product_stock(obj.product)


class ProductListSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(
        many=True,
        read_only=True,
    )

    category = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    discount_price = serializers.SerializerMethodField()
    thumb = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "price",
            "discount_price",
            "category",
            "thumb",
            "variants",
            "created_at",
            "in_stock",
        ]

    def get_category(self, obj):
        return obj.category.name if obj.category else None

    @staticmethod
    def _variant_final_price(variant):
        if (
            variant.discount_price is not None
            and variant.discount_price > 0
            and variant.discount_price < variant.price
        ):
            return variant.discount_price

        return variant.price

    def _get_display_variant(self, obj):
        cached_variant = getattr(
            obj,
            "_serializer_display_variant",
            None,
        )

        if cached_variant is not None:
            return cached_variant

        variants = list(obj.variants.all())

        available_variants = [
            variant
            for variant in variants
            if calculate_variant_available_stock(variant) > 0
        ]

        candidates = available_variants or variants

        display_variant = min(
            candidates,
            key=lambda variant: (
                self._variant_final_price(variant),
                variant.id,
            ),
            default=None,
        )

        obj._serializer_display_variant = display_variant
        return display_variant

    def get_price(self, obj):
        variant = self._get_display_variant(obj)

        return int(variant.price) if variant else None

    def get_discount_price(self, obj):
        variant = self._get_display_variant(obj)

        if (
            variant
            and variant.discount_price is not None
            and variant.discount_price > 0
            and variant.discount_price < variant.price
        ):
            return int(variant.discount_price)

        return None

    def get_thumb(self, obj):
        main_image = obj.images.filter(
            is_main=True
        ).first()

        if main_image and main_image.image:
            url = main_image.image.url

        else:
            first_image = obj.images.first()

            if first_image and first_image.image:
                url = first_image.image.url
            else:
                url = "/media/default-thumb.jpg"

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(url)

        return url

    def get_in_stock(self, obj):
        return calculate_product_stock(obj)


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    tags = serializers.SerializerMethodField()

    specifications = ProductSpecificationSerializer(
        many=True,
        read_only=True,
    )

    variants = ProductVariantSerializer(
        many=True,
        read_only=True,
    )

    images = ProductImageSerializer(
        many=True,
        read_only=True,
    )

    videos = ProductVideoSerializer(
        many=True,
        read_only=True,
    )

    is_special = serializers.SerializerMethodField()
    special_details = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "base_price",
            "category",
            "tags",
            "specifications",
            "variants",
            "images",
            "videos",
            "is_active",
            "created_at",
            "updated_at",
            "is_special",
            "special_details",
            "quantity",
        ]

    def get_is_special(self, obj):
        special = getattr(obj, "special", None)

        return bool(
            special
            and getattr(special, "is_active", False)
        )

    def get_special_details(self, obj):
        special = getattr(obj, "special", None)

        if not special:
            return None

        return {
            "title": special.title,
            "start_date": special.start_date,
            "end_date": special.end_date,
        }

    def get_tags(self, obj):
        return [
            tag.name
            for tag in obj.tags.all()
        ]

    def get_quantity(self, obj):
        return calculate_product_stock(obj)
