from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.management.base import BaseCommand, CommandError

from core.logging_config import get_logger
from core.sync_tracker import SyncRun
from products.models import Product

from basalam_integration.services.client import BasalamAPIError
from basalam_integration.services.product_service import (
    build_product_sync_plan,
    sync_product_to_basalam,
)


logger = get_logger(__name__)


class Command(BaseCommand):
    help = "همگام‌سازی همه محصولات فعال و متصل‌شده به باسلام"

    def add_arguments(self, parser):
        parser.add_argument(
            "--commit",
            action="store_true",
            help="ارسال واقعی تغییرات؛ بدون این گزینه فقط پیش‌نمایش است.",
        )

    def handle(self, *args, **options):
        products = (
            Product.objects.filter(
                is_active=True,
                basalam_mapping__is_active=True,
            )
            .select_related("category", "basalam_mapping")
            .prefetch_related(
                "variants__attributes__attribute",
                "basalam_mapping__variation_mappings",
            )
            .order_by("pk")
        )

        failed = 0

        with SyncRun(
            name="sync_basalam_products",
            supplier="basalam",
        ) as sync:
            total = products.count()
            sync.stats.received = total

            logger.info(
                "همگام‌سازی جمعی باسلام آماده شد | "
                "products=%s | commit=%s",
                total,
                options["commit"],
            )

            if total == 0:
                self.stdout.write(
                    self.style.WARNING(
                        "هیچ محصول فعال و متصل‌شده‌ای به باسلام پیدا نشد."
                    )
                )
                return

            self.stdout.write(f"تعداد محصولات قابل بررسی: {total}")
            if not options["commit"]:
                self.stdout.write(
                    self.style.WARNING(
                        "حالت پیش‌نمایش است؛ چیزی به باسلام ارسال نمی‌شود."
                    )
                )

            succeeded = 0
            added_variants = 0
            updated_variants = 0

            for product in products.iterator(chunk_size=50):
                try:
                    if options["commit"]:
                        result = sync_product_to_basalam(product)
                        added_variants += result.added_count
                        updated_variants += result.updated_count
                        message = (
                            f"افزوده: {result.added_count}، "
                            f"به‌روزرسانی: {result.updated_count}"
                        )
                    else:
                        plan = build_product_sync_plan(product)
                        added_variants += len(plan.new_variant_ids)
                        updated_variants += len(plan.existing_variant_ids)
                        message = (
                            f"واریانت جدید: {len(plan.new_variant_ids)}، "
                            "واریانت قابل به‌روزرسانی: "
                            f"{len(plan.existing_variant_ids)}"
                        )

                    succeeded += 1
                    logger.info(
                        "محصول باسلام پردازش شد | product_id=%s | "
                        "product=%s | result=%s",
                        product.pk,
                        product.name,
                        message,
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"[موفق] {product.pk} - {product.name}: {message}"
                        )
                    )
                except (
                    BasalamAPIError,
                    ImproperlyConfigured,
                    ValidationError,
                    OSError,
                    ValueError,
                ) as exc:
                    failed += 1
                    logger.exception(
                        "خطا در همگام‌سازی محصول باسلام | "
                        "product_id=%s | product=%s",
                        product.pk,
                        product.name,
                    )
                    self.stderr.write(
                        self.style.ERROR(
                            f"[ناموفق] {product.pk} - {product.name}: {exc}"
                        )
                    )

            sync.stats.failed = failed
            if options["commit"]:
                sync.stats.created = added_variants
                sync.stats.updated = updated_variants
            else:
                sync.stats.skipped = succeeded

            logger.info(
                "خلاصه همگام‌سازی جمعی باسلام | "
                "total=%s | succeeded=%s | failed=%s | "
                "added_variants=%s | updated_variants=%s | commit=%s",
                total,
                succeeded,
                failed,
                added_variants,
                updated_variants,
                options["commit"],
            )

            self.stdout.write("")
            self.stdout.write("خلاصه همگام‌سازی باسلام")
            self.stdout.write(f"کل محصولات: {total}")
            self.stdout.write(f"موفق: {succeeded}")
            self.stdout.write(f"ناموفق: {failed}")
            self.stdout.write(f"واریانت جدید: {added_variants}")
            self.stdout.write(f"واریانت به‌روزشده: {updated_variants}")

            if not options["commit"]:
                self.stdout.write(
                    self.style.WARNING(
                        "پیش‌نمایش تمام شد؛ "
                        "برای ارسال واقعی --commit را اضافه کنید."
                    )
                )

        if failed:
            raise CommandError(
                f"همگام‌سازی {failed} محصول ناموفق بود؛ گزارش بالا را ببینید."
            )
