from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from bale_integration.models import BaleProductPost
from bale_integration.services.bale_client import BaleAPIError, BaleClient
from bale_integration.services.daily_product import build_product_post, select_product_by_id


class Command(BaseCommand):
    help = "یک محصول مشخص را بدون محدودیت زمانی در کانال بله منتشر می‌کند."

    def add_arguments(self, parser):
        parser.add_argument("--product-id", type=int, required=True)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        channel_id = settings.BALE_CHANNEL_ID
        if not channel_id:
            raise CommandError("BALE_CHANNEL_ID تنظیم نشده است.")

        product, variants, image = select_product_by_id(options["product_id"])
        if product is None:
            raise CommandError("محصول فعال، موجود و دارای تصویر با این شناسه پیدا نشد.")

        photo_url, caption, product_url = build_product_post(product, variants, image)
        if options["dry_run"]:
            self.stdout.write(f"Product: {product.name}")
            self.stdout.write(f"Photo: {photo_url}")
            self.stdout.write(f"URL: {product_url}")
            self.stdout.write("--- Caption ---")
            self.stdout.write(caption)
            return

        log = BaleProductPost.objects.create(
            product=product,
            publication_date=timezone.localdate(),
            trigger=BaleProductPost.TRIGGER_MANUAL,
            channel_id=channel_id,
            attempt_count=1,
        )
        try:
            result = BaleClient().send_photo(channel_id, photo_url, caption, product_url)
        except BaleAPIError as exc:
            log.error_message = str(exc)
            log.save(update_fields=("error_message", "updated_at"))
            raise CommandError(f"خطای بله: {exc}") from exc

        log.message_id = result.get("message_id")
        log.is_successful = True
        log.save(update_fields=("message_id", "is_successful", "updated_at"))
        self.stdout.write(self.style.SUCCESS(f"ارسال شد: {product.name}"))
