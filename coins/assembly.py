import hashlib
import json
from collections import Counter
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from products.models import ProductVariant
from inventory.models import InventoryLot, InventoryMovement
from inventory.services.inventory_cost_service import InventoryCostService
from . import models as m


@transaction.atomic
def assemble_pack(*, pack_variant_id, quantity, sources, request_key):
    """sources = [{item_id, variant_id, quantity (total across all packs)}]."""
    if (
        type(quantity) is not int
        or quantity <= 0
        or not request_key
        or len(request_key) > 100
    ):
        raise ValidationError("تعداد پک و کلید عملیات معتبر الزامی است.")
    if not sources or any(
        type(row.get(k)) is not int or row[k] <= 0
        for row in sources
        for k in ("item_id", "variant_id", "quantity")
    ):
        raise ValidationError("اجزا، شناسه‌ها و تعداد مصرف باید مثبت باشند.")
    normalized = sorted(
        sources, key=lambda x: (x["item_id"], x["variant_id"], x["quantity"])
    )
    payload_hash = hashlib.sha256(
        json.dumps([pack_variant_id, quantity, normalized], sort_keys=True).encode()
    ).hexdigest()
    previous = (
        m.PackAssembly.objects.select_for_update()
        .filter(request_key=request_key)
        .first()
    )
    if previous:
        if previous.payload_hash != payload_hash:
            raise ValidationError("این کلید قبلاً برای عملیات متفاوت استفاده شده است.")
        return previous
    pv = m.CoinPackVariant.objects.select_related("variant", "pack").get(
        pk=pack_variant_id
    )
    ids = sorted(set([pv.variant_id] + [r["variant_id"] for r in sources]))
    locked = {
        v.pk: v
        for v in ProductVariant.objects.select_for_update()
        .filter(pk__in=ids)
        .order_by("pk")
    }
    if len(locked) != len(ids) or any(
        r["variant_id"] == pv.variant_id for r in sources
    ):
        raise ValidationError("واریانت مبدأ یا مقصد معتبر نیست.")
    # Serialize retries even when the request key did not exist before obtaining inventory locks.
    previous = m.PackAssembly.objects.filter(request_key=request_key).first()
    if previous:
        if previous.payload_hash != payload_hash:
            raise ValidationError("کلید تکراری با ورودی متفاوت.")
        return previous
    items = {i.pk: i for i in pv.items.select_related("issue__coin_type")}
    required = {pk: i.quantity * quantity for pk, i in items.items()}
    actual = Counter()
    per_variant = Counter()
    for row in sources:
        item = items.get(row["item_id"])
        specimen = m.CoinSpecimen.objects.filter(variant_id=row["variant_id"]).first()
        if not item or not specimen or specimen.issue_id != item.issue_id:
            raise ValidationError("سکه مبدأ با جزء پک تطبیق ندارد.")
        item.validate_issue(item.issue)
        if (
            item.condition_grade != m.Condition.UNKNOWN
            and specimen.condition_grade != item.condition_grade
        ):
            raise ValidationError(
                "حفظ‌شدگی سکه مبدأ با کیفیت تعریف‌شده پک تطبیق ندارد."
            )
        actual[item.pk] += row["quantity"]
        per_variant[specimen.variant_id] += row["quantity"]
    if not items or dict(actual) != required:
        raise ValidationError(
            "تعداد مصرف هر جزء باید دقیقاً با تعداد پک‌ها برابر باشد."
        )
    for pk, amount in per_variant.items():
        lots = InventoryLot.objects.filter(
            product_variant_id=pk, quantity_remaining__gt=0
        )
        list(lots.select_for_update().order_by("pk"))
        total = lots.aggregate(total=Sum("quantity_remaining"))["total"] or 0
        if locked[pk].stock != total or amount > total:
            raise ValidationError(
                "موجودی داخلی و لات‌ها باید تطبیق داشته و برای بسته‌بندی کافی باشند."
            )
    assembly = m.PackAssembly.objects.create(
        request_key=request_key,
        payload_hash=payload_hash,
        pack_variant=pv,
        quantity=quantity,
        total_cost=0,
        contents_snapshot={
            "year": pv.pack.year,
            "calendar": pv.pack.calendar,
            "sources": normalized,
        },
    )
    cost = Decimal("0")
    for row in normalized:
        source = locked[row["variant_id"]]
        allocations = InventoryCostService.consume_fifo(
            variant=source, quantity=row["quantity"]
        )
        for allocation in allocations:
            cost += allocation.total_cost
            m.PackAssemblyAllocation.objects.create(
                assembly=assembly,
                item=items[row["item_id"]],
                source_variant=source,
                source_lot=allocation.inventory_lot,
                quantity=allocation.quantity,
                unit_cost=allocation.unit_cost,
            )
        source.stock -= row["quantity"]
        source.save(update_fields=["stock"])
        InventoryMovement.objects.create(
            product_variant=source, type="adjustment", quantity=-row["quantity"]
        )
    target = locked[pv.variant_id]
    target.stock += quantity
    target.save(update_fields=["stock"])
    # Preserve total cost exactly even if the per-pack cost is not an integer.
    base, remainder = divmod(int(cost), quantity)
    for count, unit_cost in ((quantity - remainder, base), (remainder, base + 1)):
        if count:
            lot = InventoryLot.objects.create(
                product_variant=target,
                quantity_received=count,
                quantity_remaining=count,
                unit_cost=unit_cost,
                note=f"آماده‌سازی پک #{assembly.pk}",
            )
            assembly.output_lots.add(lot)
    InventoryMovement.objects.create(
        product_variant=target, type="adjustment", quantity=quantity
    )
    assembly.total_cost = cost
    assembly.save(update_fields=["total_cost", "updated_at"])
    return assembly
