from django.contrib import admin
from django.utils.html import format_html

from orders.models import (
    Cart,
    CartItem,
    Order,
    OrderItem,
    SalesSummary,
)


class CartItemInline(admin.TabularInline):
    """
    نمایش اقلام سبد خرید داخل صفحه جزئیات سبد.
    """

    model = CartItem
    extra = 0
    can_delete = False

    fields = (
        "product_display",
        "variant",
        "sku_display",
        "quantity",
        "unit_price_display",
        "total_price_display",
        "added_at",
    )

    readonly_fields = (
        "product_display",
        "variant",
        "sku_display",
        "quantity",
        "unit_price_display",
        "total_price_display",
        "added_at",
    )

    show_change_link = True

    @admin.display(description="محصول")
    def product_display(self, obj):
        if not obj or not obj.variant_id:
            return "-"

        return obj.variant.product.name

    @admin.display(description="SKU")
    def sku_display(self, obj):
        if not obj or not obj.variant_id:
            return "-"

        return obj.variant.sku or "-"

    @admin.display(description="قیمت واحد")
    def unit_price_display(self, obj):
        if not obj or not obj.variant_id:
            return "-"

        price = obj.variant.price

        return f"{price:,.0f} تومان"

    @admin.display(description="جمع")
    def total_price_display(self, obj):
        if not obj or not obj.variant_id:
            return "-"

        total = obj.variant.price * obj.quantity

        return f"{total:,.0f} تومان"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer_display",
        "phone_display",
        "items_count_display",
        "products_count_display",
        "total_price_display",
        "cart_status_display",
        "updated_at",
    )

    list_filter = (
        "is_active",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "id",
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "user__customer_profile__phone",
        "session_key",
        "items__variant__sku",
        "items__variant__product__name",
    )

    readonly_fields = (
        "user",
        "session_key",
        "is_active",
        "items_count_display",
        "products_count_display",
        "total_price_display",
        "created_at",
        "updated_at",
    )

    inlines = (
        CartItemInline,
    )

    ordering = (
        "-updated_at",
    )

    list_per_page = 50

    date_hierarchy = "updated_at"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "user",
                "user__customer_profile",
            )
            .prefetch_related(
                "items",
                "items__variant",
                "items__variant__product",
            )
            .distinct()
        )

    @admin.display(description="کاربر", ordering="user__username")
    def customer_display(self, obj):
        if not obj.user_id:
            return format_html(
                '<span style="color:#b7791f;">مهمان</span>'
            )

        full_name = obj.user.get_full_name().strip()

        if full_name:
            return full_name

        return obj.user.username

    @admin.display(description="شماره موبایل")
    def phone_display(self, obj):
        if not obj.user_id:
            return "-"

        try:
            return obj.user.customer_profile.phone or "-"
        except Exception:
            return "-"

    @admin.display(description="ردیف‌های سبد")
    def items_count_display(self, obj):
        return len(obj.items.all())

    @admin.display(description="تعداد کالا")
    def products_count_display(self, obj):
        return sum(
            item.quantity
            for item in obj.items.all()
        )

    @admin.display(description="مبلغ کل")
    def total_price_display(self, obj):
        total = sum(
            item.variant.price * item.quantity
            for item in obj.items.all()
            if item.variant_id
        )

        return f"{total:,.0f} تومان"

    @admin.display(description="وضعیت", boolean=False)
    def cart_status_display(self, obj):
        if not obj.is_active:
            return format_html(
                '<span style="color:#718096;">غیرفعال</span>'
            )

        if obj.is_empty():
            return format_html(
                '<span style="color:#d69e2e;">خالی</span>'
            )

        return format_html(
            '<span style="color:#27864b;font-weight:bold;">فعال</span>'
        )

    def has_add_permission(self, request):
        return False


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "cart_display",
        "product_display",
        "variant",
        "quantity",
        "unit_price_display",
        "total_price_display",
        "added_at",
    )

    list_filter = (
        "added_at",
    )

    search_fields = (
        "cart__user__username",
        "cart__user__customer_profile__phone",
        "cart__session_key",
        "variant__sku",
        "variant__product__name",
    )

    readonly_fields = (
        "cart",
        "variant",
        "quantity",
        "added_at",
        "unit_price_display",
        "total_price_display",
    )

    list_select_related = (
        "cart",
        "cart__user",
        "variant",
        "variant__product",
    )

    ordering = (
        "-added_at",
    )

    @admin.display(description="سبد")
    def cart_display(self, obj):
        if obj.cart.user_id:
            return str(obj.cart.user)

        return f"مهمان — {obj.cart.session_key or '-'}"

    @admin.display(description="محصول")
    def product_display(self, obj):
        return obj.variant.product.name

    @admin.display(description="قیمت واحد")
    def unit_price_display(self, obj):
        return f"{obj.variant.price:,.0f} تومان"

    @admin.display(description="جمع")
    def total_price_display(self, obj):
        total = obj.variant.price * obj.quantity

        return f"{total:,.0f} تومان"

    def has_add_permission(self, request):
        return False


admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(SalesSummary)
