from django.core.exceptions import ValidationError
from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from products.models import Product

from basalam_integration.services.client import (
    BasalamAPIError,
)
from basalam_integration.services.file_service import (
    get_product_images,
    upload_product_images,
)


class Command(BaseCommand):
    help = (
        "بررسی یا آپلود تصاویر یک محصول "
        "در باسلام"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "product_id",
            type=int,
            help="شناسه محصول بازبیا",
        )

        parser.add_argument(
            "--commit",
            action="store_true",
            help=(
                "آپلود واقعی تصاویر؛ "
                "بدون این گزینه فقط بررسی می‌شود."
            ),
        )

        parser.add_argument(
            "--force",
            action="store_true",
            help=(
                "آپلود مجدد حتی اگر محتوای "
                "تصویر تغییر نکرده باشد."
            ),
        )

    def handle(self, *args, **options):
        product_id = options["product_id"]
        should_commit = options["commit"]
        force = options["force"]

        try:
            product = (
                Product.objects
                .prefetch_related("images")
                .get(pk=product_id)
            )
        except Product.DoesNotExist as exc:
            raise CommandError(
                "محصول موردنظر پیدا نشد."
            ) from exc

        images = get_product_images(
            product
        )

        if not images:
            raise CommandError(
                "محصول هیچ فایل تصویر محلی ندارد."
            )

        self.stdout.write(
            f"محصول: {product.pk} - {product.name}"
        )

        self.stdout.write(
            f"تعداد تصاویر محلی: {len(images)}"
        )

        for product_image in images:
            image_type = (
                "اصلی"
                if product_image.is_main
                else "آلبوم"
            )

            self.stdout.write(
                f"- {product_image.pk}: "
                f"{image_type} - "
                f"{product_image.image.name}"
            )

        if not should_commit:
            self.stdout.write(
                self.style.WARNING(
                    "حالت بررسی بود؛ هیچ فایلی "
                    "آپلود نشد. برای ارسال واقعی "
                    "--commit را اضافه کنید."
                )
            )

            return

        try:
            results = upload_product_images(
                product,
                force=force,
            )
        except (
            BasalamAPIError,
            ValidationError,
            OSError,
        ) as exc:
            raise CommandError(
                str(exc)
            ) from exc

        for result in results:
            if result.reused:
                status = "استفاده از شناسه قبلی"
            else:
                status = "آپلود شد"

            self.stdout.write(
                f"تصویر {result.product_image_id}: "
                f"{status} - "
                f"شناسه {result.basalam_file_id}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                "پردازش تصاویر پایان یافت."
            )
        )
