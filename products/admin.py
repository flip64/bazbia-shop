from django.contrib import admin
from django.db.models import Count

from .models import (
    Attribute,
    AttributeValue,
    Category,
    Product,
    ProductImage,
    ProductSpecification,
    ProductVariant,
    ProductVideo,
    SpecialProduct,
    Tag,
)


class LargeTableAdminMixin:
    """تنظیمات مشترک برای سریع ماندن ادمین با افزایش تعداد رکوردها."""

    list_per_page = 50
    list_max_show_all = 200
    show_full_result_count = False
    save_on_top = True


@admin.register(Category)
class CategoryAdmin(LargeTableAdminMixin, admin.ModelAdmin):
    list_display = ("name", "parent", "slug")
    search_fields = ("name", "slug", "parent__name")
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ("parent",)
    autocomplete_fields = ("parent",)
    list_select_related = ("parent",)
    ordering = ("name",)


@admin.register(Tag)
class TagAdmin(LargeTableAdminMixin, admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)


@admin.register(Product)
class ProductAdmin(LargeTableAdminMixin, admin.ModelAdmin):
    list_display = (
        "id", "name", "category", "base_price", "is_active", "updated_at"
    )
    list_display_links = ("id", "name")
    list_editable = ("is_active",)
    list_filter = ("is_active", "category")
    search_fields = ("=id", "name", "slug", "description", "variants__sku")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("category", "tags")
    list_select_related = ("category",)
    readonly_fields = ("created_at", "updated_at")
    "
    """date_hierarchy = "created_at"    """
    ordering = ("-updated_at",)


@admin.register(ProductSpecification)
class ProductSpecificationAdmin(LargeTableAdminMixin, admin.ModelAdmin):
    list_display = ("product", "name", "value")
    search_fields = ("product__name", "product__slug", "name", "value")
    autocomplete_fields = ("product",)
    list_select_related = ("product",)


@admin.register(Attribute)
class AttributeAdmin(LargeTableAdminMixin, admin.ModelAdmin):
    list_display = ("name", "values_count")
    search_fields = ("name",)
    ordering = ("name",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_values_count=Count("values"))

    @admin.display(description="تعداد مقادیر")
    def values_count(self, obj):
        return obj._values_count


@admin.register(AttributeValue)
class AttributeValueAdmin(LargeTableAdminMixin, admin.ModelAdmin):
    list_display = ("value", "attribute")
    search_fields = ("value", "attribute__name")
    list_filter = ("attribute",)
    autocomplete_fields = ("attribute",)
    list_select_related = ("attribute",)
    ordering = ("attribute__name", "value")


@admin.register(ProductVariant)
class ProductVariantAdmin(LargeTableAdminMixin, admin.ModelAdmin):
    list_display = (
        "id", "product", "sku", "get_attributes", "stock",
        "low_stock_threshold", "price", "discount_price",
    )
    list_display_links = ("id", "product", "sku")
    search_fields = (
        "=id", "sku", "product__name", "product__slug",
        "attributes__value", "attributes__attribute__name",
    )
    list_filter = ("attributes__attribute",)
    autocomplete_fields = ("product", "attributes")
    list_select_related = ("product",)
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            "attributes__attribute"
        )

    @admin.display(description="ویژگی‌ها")
    def get_attributes(self, obj):
        return ", ".join(
            f"{item.attribute.name}: {item.value}"
            for item in obj.attributes.all()
        )


@admin.register(ProductImage)
class ProductImageAdmin(LargeTableAdminMixin, admin.ModelAdmin):
    list_display = ("product", "is_main", "source_url", "image")
    search_fields = ("product__name", "product__slug", "alt_text", "source_url")
    list_filter = ("is_main",)
    autocomplete_fields = ("product",)
    list_select_related = ("product",)
    readonly_fields = ("created_at",)


@admin.register(ProductVideo)
class ProductVideoAdmin(LargeTableAdminMixin, admin.ModelAdmin):
    list_display = ("product", "caption", "video", "created_at")
    search_fields = ("product__name", "product__slug", "caption")
    autocomplete_fields = ("product",)
    list_select_related = ("product",)
    readonly_fields = ("created_at",)


@admin.register(SpecialProduct)
class SpecialProductAdmin(LargeTableAdminMixin, admin.ModelAdmin):
    list_display = ("product", "title", "start_date", "end_date", "is_active")
    search_fields = ("product__name", "product__slug", "title")
    list_filter = ("is_active",)
    autocomplete_fields = ("product",)
    list_select_related = ("product",)
