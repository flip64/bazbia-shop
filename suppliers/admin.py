from django.contrib import admin

from suppliers.models import (
    Supplier,
    SupplierOffer,
    SupplierPriceHistory,
)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "website",
    )


@admin.register(SupplierOffer)
class SupplierOfferAdmin(admin.ModelAdmin):
    list_display = (
        "supplier",
        "variant",
        "supplier_product_name",
        "purchase_price",
        "supplier_stock",
        "is_available",
        "is_primary",
    )

    list_filter = (
        "supplier",
        "is_available",
        "is_primary",
    )

    search_fields = (
        "supplier_product_name",
        "supplier_product_code",
        "supplier_url",
        "variant__sku",
    )


@admin.register(SupplierPriceHistory)
class SupplierPriceHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "supplier_offer",
        "price",
        "created_at",
    )