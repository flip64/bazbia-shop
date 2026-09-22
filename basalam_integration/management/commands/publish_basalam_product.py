import json

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.management.base import BaseCommand, CommandError

from products.models import Product

from basalam_integration.services.client import BasalamAPIError
from basalam_integration.services.file_service import get_product_images
from basalam_integration.services.product_service import (
    build_product_payload,
    publish_product_to_basalam,
    validate_product_for_basalam,
)


class Command(BaseCommand):
    help = "بررسی یا ایجاد یک محصول بازبیا در غرفه باسلام"

    def add_arguments(self, parser):
        parser.add_argument("product_id", type=int, help="شناسه محصول بازبیا")
        parser.add_argument(
            "--commit",
            action="store_true",
            help="ارسال واقعی محصول؛ بدون این گزینه فقط پیش‌نمایش است.",
        )
        parser.add_argument(
            "--publish",
            action="store_true",
            help="انتشار محصول؛ در حالت پیش‌فرض محصول منتشرنشده ساخته می‌شود.",
        )

    def handle(self, *args, **options):
        try:
            product = (
                Product.objects.select_related("category")
                .prefetch_related(
                    "tags",
                    "images",
                    "variants__attributes__attribute",
                )
                .get(pk=options["product_id"])
            )
            variants = validate_product_for_basalam(product)
            images = get_product_images(product)
            if not images:
                raise ValidationError(
                    "محصول هیچ فایل تصویر محلی ندارد."
                )
        except Product.DoesNotExist as exc:
            raise CommandError("محصول موردنظر پیدا نشد.") from exc
        except ValidationError as exc:
            raise CommandError("؛ ".join(exc.messages)) from exc

        self.stdout.write(f"محصول: {product.pk} - {product.name}")
        self.stdout.write(f"تعداد واریانت‌ها: {len(variants)}")
        self.stdout.write(f"تعداد تصاویر محلی: {len(images)}")

        if not options["commit"]:
            preview_ids = list(range(1, len(images) + 1))
            payload = build_product_payload(
                product,
                image_ids=preview_ids,
                published=options["publish"],
            )
            self.stdout.write(
                json.dumps(payload, ensure_ascii=False, indent=2)
            )
            self.stdout.write(
                self.style.WARNING(
                    "حالت پیش‌نمایش بود؛ چیزی به باسلام ارسال نشد."
                )
            )
            return

        try:
            result = publish_product_to_basalam(
                product,
                published=options["publish"],
            )
        except (
            BasalamAPIError,
            ImproperlyConfigured,
            ValidationError,
            OSError,
            ValueError,
        ) as exc:
            raise CommandError(str(exc)) from exc

        status = "منتشرشده" if result.published else "منتشرنشده"
        self.stdout.write(
            self.style.SUCCESS(
                f"محصول باسلام {result.basalam_product_id} با وضعیت "
                f"{status} ایجاد شد."
            )
        )
