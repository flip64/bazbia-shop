from django.core.management.base import BaseCommand

from products.models import ProductVariant
from torob_integration.models import TorobVariantConfig


class Command(BaseCommand):
    help = "ایجاد تنظیمات ترب برای واریانت‌هایی که تنظیم ترب ندارند"

    def handle(self, *args, **options):
        created_count = 0
        existing_count = 0

        variants = ProductVariant.objects.all().only("id")

        for variant in variants.iterator(chunk_size=500):
            _, created = TorobVariantConfig.objects.get_or_create(
                variant=variant,
            )

            if created:
                created_count += 1
            else:
                existing_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{created_count} تنظیم جدید ساخته شد."
            )
        )

        self.stdout.write(
            f"{existing_count} واریانت از قبل تنظیم داشت."
        )
