# inventory/services/inventory_receipt_service.py

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
    سرویس ثبت ورود واقعی کالا به انبار داخلی بازبیا.

    هر بار که یک خرید برای انبار تأیید می‌شود:

    1. یک InventoryLot ساخته می‌شود.
    2. موجودی داخلی ProductVariant افزایش پیدا می‌کند.
    3. یک InventoryMovement از نوع purchase ثبت می‌شود.

    purchase_item اختیاری است تا موجودی‌های اولیه
    یا اصلاحات دستی هم در آینده قابل ثبت باشند.
    """

    # =====================================================
    # نرمال‌سازی تعداد
    # =====================================================

    @staticmethod
    def _normalize_quantity(
        quantity,
    ) -> int:
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
                (
                    "تعداد ورودی باید "
                    "بزرگ‌تر از صفر باشد."
                )
            )

        return quantity

    # =====================================================
    # نرمال‌سازی قیمت خرید
    # =====================================================

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
                (
                    "قیمت خرید باید "
                    "بزرگ‌تر از صفر باشد."
                )
            )

        return unit_cost

    # =====================================================
    # ثبت ورود کالا
    # =====================================================

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
        ثبت ورود کالا به انبار.

        Parameters
        ----------
        variant:
            ProductVariant موردنظر.

        quantity:
            تعداد کالای ورودی.

        unit_cost:
            بهای خرید هر واحد.

        supplier:
            تأمین‌کننده خرید.

        purchase_item:
            ردیف PurchaseItem که این Lot
            از آن ساخته شده است.

        note:
            توضیح اختیاری.

        Returns
        -------
        InventoryLot
            لات ساخته‌شده.
        """

        # -------------------------------------------------
        # اعتبارسنجی ورودی‌ها
        # -------------------------------------------------

        quantity = (
            cls._normalize_quantity(
                quantity
            )
        )

        unit_cost = (
            cls._normalize_unit_cost(
                unit_cost
            )
        )

        if variant is None:
            raise ValidationError(
                "واریانت مشخص نشده است."
            )

        # -------------------------------------------------
        # قفل کردن Variant
        # -------------------------------------------------

        try:
            variant = (
                ProductVariant.objects
                .select_for_update()
                .get(
                    pk=variant.pk
                )
            )

        except ProductVariant.DoesNotExist:
            raise ValidationError(
                "واریانت موردنظر پیدا نشد."
            )

        # -------------------------------------------------
        # جلوگیری از ساخت دوباره Lot برای PurchaseItem
        # -------------------------------------------------

        if purchase_item is not None:
            existing_lot = (
                InventoryLot.objects
                .select_for_update()
                .filter(
                    purchase_item=(
                        purchase_item
                    )
                )
                .first()
            )

            if existing_lot is not None:
                raise ValidationError(
                    (
                        "برای این ردیف خرید "
                        "قبلاً یک لات موجودی "
                        "ایجاد شده است. "
                        f"Lot #{existing_lot.pk}"
                    )
                )

            # -------------------------------------------------
            # کنترل تطابق واریانت PurchaseItem
            # -------------------------------------------------

            if (
                purchase_item.variant_id
                != variant.pk
            ):
                raise ValidationError(
                    (
                        "واریانت PurchaseItem "
                        "با واریانت ورودی "
                        "انبار یکسان نیست."
                    )
                )

            # -------------------------------------------------
            # کنترل تطابق تعداد
            # -------------------------------------------------

            if (
                int(purchase_item.quantity)
                != quantity
            ):
                raise ValidationError(
                    (
                        "تعداد ورود انبار با "
                        "تعداد PurchaseItem "
                        "یکسان نیست."
                    )
                )

            # -------------------------------------------------
            # کنترل تطابق قیمت خرید
            # -------------------------------------------------

            purchase_item_cost = (
                cls._normalize_unit_cost(
                    purchase_item.unit_cost
                )
            )

            if (
                purchase_item_cost
                != unit_cost
            ):
                raise ValidationError(
                    (
                        "قیمت خرید ورود انبار "
                        "با قیمت PurchaseItem "
                        "یکسان نیست."
                    )
                )

        # -------------------------------------------------
        # ساخت InventoryLot
        # -------------------------------------------------

        lot = (
            InventoryLot.objects.create(
                product_variant=variant,
                supplier=supplier,
                purchase_item=(
                    purchase_item
                ),
                quantity_received=(
                    quantity
                ),
                quantity_remaining=(
                    quantity
                ),
                unit_cost=unit_cost,
                note=str(
                    note or ""
                ).strip(),
            )
        )

        # -------------------------------------------------
        # افزایش موجودی داخلی Variant
        # -------------------------------------------------

        current_stock = max(
            int(
                variant.stock
                or 0
            ),
            0,
        )

        variant.stock = (
            current_stock
            + quantity
        )

        variant.save(
            update_fields=[
                "stock",
            ]
        )

        # -------------------------------------------------
        # ثبت حرکت موجودی
        # -------------------------------------------------

        InventoryMovement.objects.create(
            product_variant=variant,
            type=(
                InventoryMovement
                .TYPE_PURCHASE
            ),
            quantity=quantity,
            related_order=None,
        )

        return lot