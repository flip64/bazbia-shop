from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect

from purchases.models import Purchase, PurchaseItem
from purchases.services.purchase_confirmation_service import (
    PurchaseConfirmationService,
)


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1
    fields = (
        "variant",
        "quantity",
        "unit_cost",
        "line_total",
    )
    readonly_fields = ("line_total",)
    autocomplete_fields = ("variant",)

    @admin.display(description="جمع ردیف")
    def line_total(self, obj):
        if not obj or not obj.pk:
            return "-"

        return f"{obj.total_amount:,.0f}"

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status == Purchase.STATUS_CONFIRMED:
            return (
                "variant",
                "quantity",
                "unit_cost",
                "line_total",
            )

        return super().get_readonly_fields(request, obj)

    def has_add_permission(self, request, obj=None):
        return not (
            obj
            and obj.status == Purchase.STATUS_CONFIRMED
        )

    def has_delete_permission(self, request, obj=None):
        return not (
            obj
            and obj.status == Purchase.STATUS_CONFIRMED
        )


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    change_form_template = (
        "admin/purchases/purchase/change_form.html"
    )
    inlines = (PurchaseItemInline,)
    list_display = (
        "id",
        "supplier",
        "invoice_number",
        "status",
        "total_amount_display",
        "created_at",
        "confirmed_at",
    )
    list_filter = (
        "status",
        "supplier",
        "created_at",
    )
    search_fields = (
        "invoice_number",
        "supplier__name",
        "items__variant__sku",
        "items__variant__product__name",
    )
    ordering = ("-created_at", "-id")

    @admin.display(description="جمع خرید")
    def total_amount_display(self, obj):
        return f"{obj.total_amount:,.0f}"

    def get_readonly_fields(self, request, obj=None):
        base_fields = (
            "status",
            "created_at",
            "confirmed_at",
        )

        if obj and obj.status == Purchase.STATUS_CONFIRMED:
            return (
                "supplier",
                "payment_type",
                "invoice_number",
                "note",
                *base_fields,
            )

        return base_fields

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status == Purchase.STATUS_CONFIRMED:
            return False

        return super().has_delete_permission(request, obj)

    def response_change(self, request, obj):
        if "_confirm_purchase" not in request.POST:
            return super().response_change(request, obj)

        try:
            confirmed_purchase = (
                PurchaseConfirmationService.confirm(
                    purchase=obj
                )
            )
        except ValidationError as error:
            self.message_user(
                request,
                " ".join(error.messages),
                level=messages.ERROR,
            )
        else:
            self.message_user(
                request,
                (
                    f"خرید #{confirmed_purchase.pk} تأیید شد "
                    "و اقلام آن وارد انبار شدند."
                ),
                level=messages.SUCCESS,
            )

        return HttpResponseRedirect(".")


@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "purchase",
        "variant",
        "quantity",
        "unit_cost",
    )
    list_select_related = (
        "purchase",
        "variant",
        "variant__product",
    )
    search_fields = (
        "purchase__invoice_number",
        "variant__sku",
        "variant__product__name",
    )

    def has_add_permission(self, request):
        # ردیف‌ها باید از داخل صفحه خود خرید ساخته شوند.
        return False

    def has_change_permission(self, request, obj=None):
        # ویرایش ردیف فقط از Inline فاکتور خرید انجام می‌شود.
        return False

    def has_delete_permission(self, request, obj=None):
        return False
