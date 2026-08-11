from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from inventory.models import InventoryLot


@dataclass(frozen=True)
class InventoryCostAllocationResult:
    inventory_lot: InventoryLot
    quantity: int
    unit_cost: Decimal

    @property
    def total_cost(self) -> Decimal:
        return (
            Decimal(self.quantity)
            * self.unit_cost
        )


class InventoryCostService:
    """
    سرویس محاسبه و مصرف بهای موجودی داخلی.

    روش ارزش‌گذاری:
    FIFO

    یعنی قدیمی‌ترین InventoryLot
    زودتر مصرف می‌شود.
    """

    @classmethod
    @transaction.atomic
    def consume_fifo(
        cls,
        *,
        variant,
        quantity,
    ) -> list[InventoryCostAllocationResult]:
        """
        مصرف موجودی داخلی از InventoryLotها
        به روش FIFO.

        توجه:
        این متد فقط quantity_remaining لات‌ها
        را کم می‌کند.

        تغییر variant.stock باید در لایه
        مدیریت موجودی سفارش انجام شود.
        """

        quantity = int(quantity)

        if quantity <= 0:
            raise ValidationError(
                "تعداد مصرف موجودی باید بزرگ‌تر از صفر باشد."
            )

        lots = (
            InventoryLot.objects
            .select_for_update()
            .filter(
                product_variant=variant,
                quantity_remaining__gt=0,
            )
            .order_by(
                "received_at",
                "id",
            )
        )

        remaining_quantity = quantity

        allocations = []

        for lot in lots:
            if remaining_quantity <= 0:
                break

            lot_available = int(
                lot.quantity_remaining
                or 0
            )

            if lot_available <= 0:
                continue

            consume_quantity = min(
                lot_available,
                remaining_quantity,
            )

            lot.quantity_remaining = (
                lot_available
                - consume_quantity
            )

            lot.save(
                update_fields=[
                    "quantity_remaining",
                ]
            )

            allocations.append(
                InventoryCostAllocationResult(
                    inventory_lot=lot,
                    quantity=consume_quantity,
                    unit_cost=Decimal(
                        str(lot.unit_cost)
                    ),
                )
            )

            remaining_quantity -= (
                consume_quantity
            )

        if remaining_quantity > 0:
            raise ValidationError(
                (
                    "موجودی ریالی ثبت‌شده در لات‌ها "
                    "برای این واریانت کافی نیست. "
                    f"تعداد درخواستی: {quantity} - "
                    f"کسری لات: {remaining_quantity}"
                )
            )

        return allocations

    @staticmethod
    def calculate_total_cost(
        allocations,
    ) -> Decimal:
        """
        جمع بهای تمام‌شده Allocationهای FIFO.
        """

        total = Decimal("0")

        for allocation in allocations:
            total += allocation.total_cost

        return total
