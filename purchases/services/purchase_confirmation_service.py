from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from inventory.models import InventoryLot
from inventory.services.inventory_receipt_service import (
    InventoryReceiptService,
)
from purchases.models import Purchase, PurchaseItem


class PurchaseConfirmationService:
    """تأیید نهایی خرید و ورود یک‌مرحله‌ای اقلام آن به انبار."""

    @classmethod
    @transaction.atomic
    def confirm(cls, *, purchase: Purchase) -> Purchase:
        purchase = (
            Purchase.objects
            .select_for_update()
            .select_related("supplier")
            .get(pk=purchase.pk)
        )

        # تأیید دوباره نباید موجودی را دوباره افزایش دهد.
        if purchase.status == Purchase.STATUS_CONFIRMED:
            return purchase

        if purchase.status != Purchase.STATUS_DRAFT:
            raise ValidationError(
                "فقط خرید پیش‌نویس قابل تأیید است."
            )

        items = list(
            PurchaseItem.objects
            .select_for_update()
            .select_related(
                "purchase",
                "purchase__supplier",
                "variant",
                "variant__product",
            )
            .filter(purchase=purchase)
            .order_by("id")
        )

        if not items:
            raise ValidationError(
                "خرید بدون ردیف کالا قابل تأیید نیست."
            )

        item_ids = [item.pk for item in items]

        if InventoryLot.objects.filter(
            purchase_item_id__in=item_ids
        ).exists():
            raise ValidationError(
                "برای یکی از ردیف‌های این خرید قبلاً لات ساخته شده است."
            )

        for item in items:
            item.full_clean()

            note_parts = [f"خرید #{purchase.pk}"]

            if purchase.invoice_number:
                note_parts.append(
                    f"فاکتور {purchase.invoice_number}"
                )

            InventoryReceiptService.receive(
                variant=item.variant,
                quantity=item.quantity,
                unit_cost=item.unit_cost,
                supplier=purchase.supplier,
                purchase_item=item,
                note=" - ".join(note_parts),
            )

        purchase.status = Purchase.STATUS_CONFIRMED
        purchase.confirmed_at = timezone.now()
        purchase.save(
            update_fields=[
                "status",
                "confirmed_at",
            ]
        )

        return purchase

