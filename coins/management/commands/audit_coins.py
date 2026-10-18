from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from coins.models import CoinSpecimen, CoinPackVariant
from coins.services import readiness_errors
from coins.guards import inventory_write


class Command(BaseCommand):
    help = "بررسی خواندنی آمادگی و موجودی سکه‌ها و پک‌ها؛ بدون تغییر داده"

    def handle(self, **options):
        errors = []
        count = 0
        for model in (CoinSpecimen, CoinPackVariant):
            for obj in model.objects.select_related("variant__product"):
                count += 1
                try:
                    with inventory_write([obj.variant_id]):
                        obj.full_clean()
                    from inventory.models import InventoryLot
                    from django.db.models import Sum

                    lot_stock = (
                        InventoryLot.objects.filter(
                            product_variant_id=obj.variant_id, quantity_remaining__gt=0
                        ).aggregate(total=Sum("quantity_remaining"))["total"]
                        or 0
                    )
                    if lot_stock != obj.variant.stock:
                        errors.append(f"{model.__name__}#{obj.pk}: stock/lot mismatch")
                    if obj.is_published:
                        problems = readiness_errors(obj)
                        if problems:
                            errors.append(f"{model.__name__}#{obj.pk}: {problems}")
                except ValidationError as error:
                    errors.append(f"{model.__name__}#{obj.pk}: {error.messages}")
        if errors:
            raise CommandError("\n".join(errors))
        self.stdout.write(self.style.SUCCESS(f"{count} listing(s) checked; no errors."))
