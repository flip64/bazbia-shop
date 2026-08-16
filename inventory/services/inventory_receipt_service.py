from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from inventory.models import (
    InventoryLot,
    InventoryMovement,
)
from products.models import ProductVariant


class InventoryReceiptService:
    """
    سرویس ورود کالا به انبار داخلی بازبیا.

    هر ورود کالا:
    1. یک InventoryLot با قیمت خرید می‌سازد.
    2. variant.stock را افزایش می‌دهد.
    3. یک InventoryMovement از نوع purchase ثبت می‌کند.
    """

    @staticmethod
    def _normalize_quantity(quantity) -> int:
        try:
            quantity = int(quantity)
        except (
            TypeError,
            ValueError,
        ):
            raise ValidationError(
                "تعداد ورودی معتبر نیست."
            )

        if quantity <= 0:
            raise ValidationError(
                "تعداد ورودی باید بزرگ‌تر از صفر باشد."
            )

        return quantity

    @staticmethod
    def _normalize_unit_cost(
        unit_cost,
    ) -> Decimal:
        try:
            unit_cost = Decimal(
                str(unit_cost)
            ).quantize(
                Decimal("1")
            )
        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ):
            raise ValidationError(
                "قیمت خرید معتبر نیست."
            )

        if unit_cost <= 0:
            raise ValidationError(
                "قیمت خرید باید بزرگ‌تر از صفر باشد."
            )

        return unit_cost

    @classmethod
    @transaction.atomic
    def receive(
        cls,
        *,
        variant,
        quantity,
        unit_cost,
        supplier=None,
        purchase_item=None,
        note="",
    ) -> InventoryLot:
        """
        ثبت ورود یک محموله به انبار داخلی.
        """

        quantity = cls._normalize_quantity(
            quantity
        )

        unit_cost = cls._normalize_unit_cost(
            unit_cost
        )

        # واریانت را دوباره با lock می‌گیریم تا
        # ورودهای همزمان موجودی را خراب نکنند.
        variant = (
            ProductVariant.objects
            .select_for_update()
            .get(pk=variant.pk)
        )

        # -----------------------------------------
        # ساخت Lot
        # -----------------------------------------

        lot = InventoryLot.objects.create(
            product_variant=variant,
            supplier=supplier,
            quantity_received=quantity,
            quantity_remaining=quantity,
            unit_cost=unit_cost,
            note=str(note or "").strip(),
        )

        # -----------------------------------------
        # افزایش موجودی تعدادی
        # -----------------------------------------

        variant.stock = (
            int(variant.stock or 0)
            + quantity
        )

        variant.save(
            update_fields=[
                "stock",
            ]
        )

        # -----------------------------------------
        # ثبت حرکت موجودی
        # -----------------------------------------

        InventoryMovement.objects.create(
            product_variant=variant,
            type="purchase",
            quantity=quantity,
        )

        return lot
