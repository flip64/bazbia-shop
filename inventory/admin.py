# inventory/admin.py

from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path

from inventory.forms import InventoryReceiptForm
from inventory.models import (
    InventoryLot,
    InventoryMovement,
)
from inventory.services.inventory_receipt_service import (
    InventoryReceiptService,
)


# =========================================================
# Inventory Lot
# =========================================================

@admin.register(InventoryLot)
class InventoryLotAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product_variant",
        "supplier",
        "quantity_received",
        "quantity_remaining",
        "unit_cost",
        "received_at",
    )

    list_filter = (
        "supplier",
        "received_at",
    )

    search_fields = (
        "product_variant__sku",
        "product_variant__product__name",
        "supplier__name",
    )

    readonly_fields = (
        "product_variant",
        "supplier",
        "quantity_received",
        "quantity_remaining",
        "unit_cost",
        "received_at",
        "note",
    )

    ordering = (
        "-received_at",
        "-id",
    )

    change_list_template = (
        "admin/inventory/"
        "inventorylot/change_list.html"
    )

    # -----------------------------------------------------
    # جلوگیری از ساخت مستقیم Lot
    # -----------------------------------------------------

    def has_add_permission(
        self,
        request,
    ):
        return False

    # -----------------------------------------------------
    # جلوگیری از حذف Lot
    # -----------------------------------------------------

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False

    # -----------------------------------------------------
    # URL اختصاصی ثبت ورود کالا
    # -----------------------------------------------------

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "receive/",
                self.admin_site.admin_view(
                    self.receive_inventory
                ),
                name="inventory_receive",
            ),
        ]

        return custom_urls + urls

    # -----------------------------------------------------
    # صفحه ثبت ورود کالا
    # -----------------------------------------------------

    def receive_inventory(
        self,
        request,
    ):
        if request.method == "POST":
            form = InventoryReceiptForm(
                request.POST
            )

            if form.is_valid():
                try:
                    lot = (
                        InventoryReceiptService
                        .receive(
                            variant=(
                                form.cleaned_data[
                                    "variant"
                                ]
                            ),
                            supplier=(
                                form.cleaned_data[
                                    "supplier"
                                ]
                            ),
                            quantity=(
                                form.cleaned_data[
                                    "quantity"
                                ]
                            ),
                            unit_cost=(
                                form.cleaned_data[
                                    "unit_cost"
                                ]
                            ),
                            note=(
                                form.cleaned_data[
                                    "note"
                                ]
                            ),
                        )
                    )

                    messages.success(
                        request,
                        (
                            "ورود کالا با موفقیت "
                            "ثبت شد. "
                            f"Lot #{lot.pk}"
                        ),
                    )

                    return redirect(
                        "admin:"
                        "inventory_inventorylot_changelist"
                    )

                except Exception as error:
                    messages.error(
                        request,
                        str(error),
                    )

        else:
            form = InventoryReceiptForm()

        context = {
            **self.admin_site.each_context(
                request
            ),
            "title":
                "ثبت ورود کالا به انبار",
            "form": form,
            "opts": self.model._meta,
        }

        return render(
            request,
            (
                "admin/inventory/"
                "inventorylot/"
                "receive.html"
            ),
            context,
        )


# =========================================================
# Inventory Movement
# =========================================================

@admin.register(InventoryMovement)
class InventoryMovementAdmin(
    admin.ModelAdmin
):
    list_display = (
        "id",
        "product_variant",
        "type",
        "quantity",
        "order",
        "created_at",
    )

    list_filter = (
        "type",
        "created_at",
    )

    search_fields = (
        "product_variant__sku",
        "product_variant__product__name",
        "order__id",
    )

    readonly_fields = (
        "product_variant",
        "type",
        "quantity",
        "order",
        "created_at",
    )

    ordering = (
        "-created_at",
        "-id",
    )

    # -----------------------------------------------------
    # حرکت موجودی فقط توسط Service ساخته شود
    # -----------------------------------------------------

    def has_add_permission(
        self,
        request,
    ):
        return False

    # -----------------------------------------------------
    # حذف حرکت موجودی ممنوع
    # -----------------------------------------------------

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False
