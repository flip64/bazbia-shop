# basalam_integration/admin.py

from django.contrib import admin

from .models import (
    BasalamCategory,
    BasalamCategoryMapping,
    BasalamOrderMapping,
    BasalamProductMapping,
    BasalamVariationMapping,
)



@admin.register(BasalamImageMapping)
class BasalamImageMappingAdmin(admin.ModelAdmin):
    list_display = (
        "product_image",
        "basalam_file_id",
        "last_synced_at",
    )

    search_fields = (
        "product_image__product__name",
        "basalam_file_id",
        "content_hash",
    )

    list_select_related = (
        "product_image",
        "product_image__product",
    )

    readonly_fields = (
        "product_image",
        "basalam_file_id",
        "content_hash",
        "last_synced_at",
        "last_error",
        "created_at",
    )

    def has_add_permission(
        self,
        request,
    ):
        return False
# =========================================================
# دسته‌ها و کارمزدهای باسلام
# =========================================================
@admin.register(BasalamCategory)
class BasalamCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "basalam_category_id",
        "commission_percent",
        "is_active",
        "updated_at",
    )

    list_editable = (
        "commission_percent",
        "is_active",
    )

    search_fields = (
        "title",
        "basalam_category_id",
    )

    list_filter = (
        "is_active",
        "commission_percent",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "title",
    )


# =========================================================
# اتصال دسته‌های بازبیا به باسلام
# =========================================================
@admin.register(BasalamCategoryMapping)
class BasalamCategoryMappingAdmin(admin.ModelAdmin):
    list_display = (
        "bazbia_category",
        "basalam_category",
        "get_commission_percent",
        "is_active",
        "updated_at",
    )

    list_editable = (
        "is_active",
    )

    search_fields = (
        "bazbia_category__name",
        "basalam_category__title",
        "basalam_category__basalam_category_id",
    )

    list_filter = (
        "is_active",
        "basalam_category__is_active",
    )

    list_select_related = (
        "bazbia_category",
        "basalam_category",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    @admin.display(
        description="کارمزد",
        ordering="basalam_category__commission_percent",
    )
    def get_commission_percent(self, obj):
        return f"{obj.basalam_category.commission_percent}٪"


# =========================================================
# واریانت‌های متصل به محصول باسلام
# =========================================================
class BasalamVariationMappingInline(admin.TabularInline):
    model = BasalamVariationMapping
    extra = 0

    fields = (
        "variant",
        "basalam_variation_id",
        "last_synced_price",
        "last_synced_stock",
        "last_synced_at",
        "last_error",
    )

    readonly_fields = (
        "last_synced_price",
        "last_synced_stock",
        "last_synced_at",
        "last_error",
    )

    autocomplete_fields = (
        "variant",
    )


# =========================================================
# محصولات متصل به باسلام
# =========================================================
@admin.register(BasalamProductMapping)
class BasalamProductMappingAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "basalam_product_id",
        "get_category",
        "is_active",
        "last_synced_at",
    )

    list_editable = (
        "is_active",
    )

    search_fields = (
        "product__name",
        "product__slug",
        "basalam_product_id",
    )

    list_filter = (
        "is_active",
        "product__category",
    )

    list_select_related = (
        "product",
        "product__category",
    )

    autocomplete_fields = (
        "product",
    )

    readonly_fields = (
        "last_synced_at",
        "last_error",
        "created_at",
        "updated_at",
    )

    inlines = (
        BasalamVariationMappingInline,
    )

    @admin.display(
        description="دسته بازبیا",
        ordering="product__category__name",
    )
    def get_category(self, obj):
        if obj.product.category:
            return obj.product.category.name

        return "-"


# =========================================================
# واریانت‌های متصل به باسلام
# =========================================================
@admin.register(BasalamVariationMapping)
class BasalamVariationMappingAdmin(admin.ModelAdmin):
    list_display = (
        "variant",
        "get_sku",
        "basalam_variation_id",
        "last_synced_price",
        "last_synced_stock",
        "last_synced_at",
    )

    search_fields = (
        "variant__sku",
        "variant__product__name",
        "basalam_variation_id",
    )

    list_select_related = (
        "variant",
        "variant__product",
        "product_mapping",
    )

    autocomplete_fields = (
        "variant",
        "product_mapping",
    )

    readonly_fields = (
        "last_synced_price",
        "last_synced_stock",
        "last_synced_at",
        "last_error",
        "created_at",
        "updated_at",
    )

    @admin.display(
        description="SKU",
        ordering="variant__sku",
    )
    def get_sku(self, obj):
        return obj.variant.sku


# =========================================================
# سفارش‌های دریافت‌شده از باسلام
# =========================================================
@admin.register(BasalamOrderMapping)
class BasalamOrderMappingAdmin(admin.ModelAdmin):
    list_display = (
        "basalam_order_id",
        "order",
        "basalam_status",
        "last_synced_at",
    )

    search_fields = (
        "basalam_order_id",
        "order__id",
    )

    list_filter = (
        "basalam_status",
        "created_at",
    )

    list_select_related = (
        "order",
    )

    readonly_fields = (
        "order",
        "basalam_order_id",
        "basalam_status",
        "raw_payload",
        "last_synced_at",
        "created_at",
    )

    ordering = (
        "-created_at",
    )

    def has_add_permission(self, request):
        # این مدل فقط باید توسط سرویس دریافت سفارش ساخته شود.
        return False
