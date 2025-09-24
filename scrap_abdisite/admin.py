from django.contrib import admin
from scrap_abdisite.models import WatchedURL,PriceHistory



# admin.site.register(WatchedURL)
# admin.site.register(PriceHistory)


@admin.register(WatchedURL)
class WatchedURLAdmin(admin.ModelAdmin):
    list_display = (
        'product_name',      # از property product استفاده می‌کنیم
        'variant_sku',       # SKU واریانت
        'supplier_name',     # نام تأمین‌کننده
        'price',
        'last_checked',
        'user',
    )
    list_filter = ('supplier', 'last_checked', 'user')
    search_fields = ('variant__product__name', 'variant__sku', 'supplier__name', 'url')
    ordering = ('-last_checked',)
    readonly_fields = ('last_checked', 'created_at')

    def product_name(self, obj):
        return obj.product.name if obj.product else "بدون محصول"
    product_name.short_description = 'محصول'

    def variant_sku(self, obj):
        return obj.variant.sku if obj.variant else "بدون واریانت"
    variant_sku.short_description = 'واریانت'

    def supplier_name(self, obj):
        return obj.supplier.name
    supplier_name.short_description = 'تأمین‌کننده'


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('watched_url', 'price', 'checked_at')
    list_filter = ('checked_at', 'watched_url__supplier')
    search_fields = ('watched_url__variant__product__name', 'watched_url__variant__sku')
    ordering = ('-checked_at',)

