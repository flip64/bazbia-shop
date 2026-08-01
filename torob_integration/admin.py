from django.contrib import admin
from django.utils.html import format_html

from .models import TorobRequestLog, TorobVariantConfig


@admin.register(TorobVariantConfig)
class TorobVariantConfigAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "variant_display",
        "product_display",
        "sku_display",
        "stock_display",
        "price_display",
        "is_enabled",
        "page_unique",
        "torob_updated_at",
    )

    list_filter = (
        "is_enabled",
        "created_at",
        "torob_updated_at",
    )

    search_fields = (
        "page_unique",
        "variant__sku",
        "variant__product__name",
        "variant__product__slug",
    )

    readonly_fields = (
        "page_unique",
        "product_group_id_display",
        "created_at",
        "updated_at",
        "torob_updated_at",
    )

    autocomplete_fields = (
        "variant",
    )

    list_select_related = (
        "variant",
        "variant__product",
    )

    ordering = (
        "-torob_updated_at",
    )

    list_per_page = 50

    actions = (
        "enable_selected_variants",
        "disable_selected_variants",
        "touch_selected_variants",
    )

    fieldsets = (
        (
            "واریانت محصول",
            {
                "fields": (
                    "variant",
                    "is_enabled",
                ),
            },
        ),
        (
            "شناسه‌های ترب",
            {
                "fields": (
                    "page_unique",
                    "product_group_id_display",
                ),
            },
        ),
        (
            "زمان‌ها",
            {
                "fields": (
                    "torob_updated_at",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    @admin.display(
        description="واریانت",
        ordering="variant__id",
    )
    def variant_display(self, obj):
        return str(obj.variant)

    @admin.display(
        description="محصول",
        ordering="variant__product__name",
    )
    def product_display(self, obj):
        return obj.variant.product.name

    @admin.display(
        description="SKU",
        ordering="variant__sku",
    )
    def sku_display(self, obj):
        return obj.variant.sku or "-"

    @admin.display(
        description="موجودی",
        ordering="variant__stock",
    )
    def stock_display(self, obj):
        stock = obj.variant.stock

        if stock > 0:
            return format_html(
                '<strong style="color:#15803d">{}</strong>',
                stock,
            )

        return format_html(
            '<strong style="color:#b91c1c">ناموجود</strong>'
        )

    @admin.display(
        description="قیمت",
        ordering="variant__price",
    )
    def price_display(self, obj):
        variant = obj.variant

        if (
            variant.discount_price is not None
            and variant.discount_price > 0
            and variant.discount_price < variant.price
        ):
            return format_html(
                '<span style="text-decoration:line-through;color:#777">'
                "{:,}"
                "</span><br>"
                '<strong style="color:#15803d">{:,}</strong>',
                int(variant.price),
                int(variant.discount_price),
            )

        return f"{int(variant.price):,}"

    @admin.display(
        description="شناسه گروه محصول در ترب",
    )
    def product_group_id_display(self, obj):
        if not obj or not obj.variant_id:
            return "-"

        return str(obj.variant.product_id)

    @admin.action(description="فعال‌کردن واریانت‌های انتخاب‌شده در ترب")
    def enable_selected_variants(self, request, queryset):
        updated = queryset.update(
            is_enabled=True,
        )

        self.message_user(
            request,
            f"{updated} واریانت برای ترب فعال شد.",
        )

    @admin.action(description="غیرفعال‌کردن واریانت‌های انتخاب‌شده در ترب")
    def disable_selected_variants(self, request, queryset):
        updated = queryset.update(
            is_enabled=False,
        )

        self.message_user(
            request,
            f"{updated} واریانت در ترب غیرفعال شد.",
        )

    @admin.action(description="ثبت تغییر جدید برای واریانت‌های انتخاب‌شده")
    def touch_selected_variants(self, request, queryset):
        from django.utils import timezone

        updated = queryset.update(
            torob_updated_at=timezone.now(),
        )

        self.message_user(
            request,
            f"زمان بروزرسانی {updated} واریانت تغییر کرد.",
        )


@admin.register(TorobRequestLog)
class TorobRequestLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "request_type",
        "response_status_display",
        "products_count",
        "total_products",
        "page",
        "sort",
        "auth_status",
        "duration_ms_display",
        "ip_address",
        "created_at",
    )

    list_filter = (
        "request_type",
        "response_status",
        "auth_status",
        "sort",
        "created_at",
    )

    search_fields = (
        "ip_address",
        "endpoint",
        "error_message",
        "token_version",
    )

    readonly_fields = (
        "request_type",
        "method",
        "endpoint",
        "request_body",
        "page",
        "sort",
        "requested_items_count",
        "response_status",
        "products_count",
        "total_products",
        "max_pages",
        "auth_status",
        "token_version",
        "error_message",
        "duration_ms",
        "ip_address",
        "user_agent",
        "created_at",
    )

    ordering = (
        "-created_at",
    )

    date_hierarchy = "created_at"

    list_per_page = 100

    fieldsets = (
        (
            "اطلاعات درخواست",
            {
                "fields": (
                    "request_type",
                    "method",
                    "endpoint",
                    "request_body",
                    "page",
                    "sort",
                    "requested_items_count",
                ),
            },
        ),
        (
            "اطلاعات پاسخ",
            {
                "fields": (
                    "response_status",
                    "products_count",
                    "total_products",
                    "max_pages",
                    "duration_ms",
                    "error_message",
                ),
            },
        ),
        (
            "امنیت و مبدا درخواست",
            {
                "fields": (
                    "auth_status",
                    "token_version",
                    "ip_address",
                    "user_agent",
                ),
            },
        ),
        (
            "زمان",
            {
                "fields": (
                    "created_at",
                ),
            },
        ),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(
        description="وضعیت پاسخ",
        ordering="response_status",
    )
    def response_status_display(self, obj):
        status_code = obj.response_status

        if 200 <= status_code < 300:
            color = "#15803d"
        elif 400 <= status_code < 500:
            color = "#b45309"
        else:
            color = "#b91c1c"

        return format_html(
            '<strong style="color:{}">{}</strong>',
            color,
            status_code,
        )

    @admin.display(
        description="زمان پاسخ",
        ordering="duration_ms",
    )
    def duration_ms_display(self, obj):
        if obj.duration_ms is None:
            return "-"

        return f"{obj.duration_ms:,} ms"
