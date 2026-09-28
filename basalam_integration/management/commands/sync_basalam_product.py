from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.management.base import BaseCommand, CommandError

from products.models import Product

from basalam_integration.services.client import BasalamAPIError
from basalam_integration.services.product_service import (
    build_product_sync_plan,
    sync_product_to_basalam,
)


class Command(BaseCommand):
    help = "افزودن تنوع‌های جدید و همگام‌سازی قیمت و موجودی محصول باسلام"

    def add_arguments(self, parser):
        parser.add_argument("product_id", type=int, help="شناسه محصول بازبیا")
        parser.add_argument(
            "--commit",
            action="store_true",
            help="ارسال واقعی تغییرات؛ بدون این گزینه فقط پیش‌نمایش است.",
        )

    def handle(self, *args, **options):
        try:
            product = (
                Product.objects.select_related("category", "basalam_mapping")
                .prefetch_related(
                    "variants__attributes__attribute",
                    "basalam_mapping__variation_mappings",
                )
                .get(pk=options["product_id"])
            )
            plan = build_product_sync_plan(product)
        except Product.DoesNotExist as exc:
            raise CommandError("محصول موردنظر پیدا نشد.") from exc
        except ValidationError as exc:
            raise CommandError("؛ ".join(exc.messages)) from exc

        self.stdout.write(f"محصول: {product.pk} - {product.name}")
        self.stdout.write(f"محصول باسلام: {plan.basalam_product_id}")
        self.stdout.write(
            f"واریانت جدید: {len(plan.new_variant_ids)}"
        )
        self.stdout.write(
            f"واریانت قابل به‌روزرسانی: {len(plan.existing_variant_ids)}"
        )

        if not options["commit"]:
            self.stdout.write(
                self.style.WARNING(
                    "حالت پیش‌نمایش بود؛ چیزی به باسلام ارسال نشد."
                )
            )
            return

        try:
            result = sync_product_to_basalam(product)
        except (
            BasalamAPIError,
            ImproperlyConfigured,
            ValidationError,
            ValueError,
        ) as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                "همگام‌سازی انجام شد؛ "
                f"افزوده‌شده: {result.added_count}، "
                f"به‌روزرسانی‌شده: {result.updated_count}"
            )
        )
