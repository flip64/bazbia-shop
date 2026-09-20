from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import F
from django.utils import timezone

from bale_integration.models import BaleProductPost
from bale_integration.services.bale_client import BaleAPIError, BaleClient
from bale_integration.services.daily_product import (
    build_product_post,
    select_daily_product,
)


class Command(BaseCommand):
    help = "یک محصول موجود را انتخاب و در کانال بله منتشر می‌کند."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--exclude-days", type=int, default=30)

    def handle(self, *args, **options):
        channel_id = settings.BALE_CHANNEL_ID
        if not channel_id:
            raise CommandError("BALE_CHANNEL_ID تنظیم نشده است.")

        today = timezone.localdate()
        previous = BaleProductPost.objects.filter(
            publication_date=today,
            is_successful=True,
        ).first()
        if previous:
            self.stdout.write(
                self.style.WARNING("محصول امروز قبلاً ارسال شده است.")
            )
            return

        product, variants, image = select_daily_product(options["exclude_days"])
        if product is None:
            raise CommandError("محصول فعال، موجود و دارای تصویر پیدا نشد.")

        photo_url, caption, product_url = build_product_post(
            product,
            variants,
            image,
        )
        if options["dry_run"]:
            self.stdout.write(f"Product: {product.name}")
            self.stdout.write(f"Photo: {photo_url}")
            self.stdout.write(f"URL: {product_url}")
            self.stdout.write("--- Caption ---")
            self.stdout.write(caption)
            return

        log, _ = BaleProductPost.objects.update_or_create(
            publication_date=today,
            defaults={
                "product": product,
                "channel_id": channel_id,
                "message_id": None,
                "is_successful": False,
                "error_message": "",
            },
        )
        BaleProductPost.objects.filter(pk=log.pk).update(
            attempt_count=F("attempt_count") + 1
        )

        try:
            result = BaleClient().send_photo(
                chat_id=channel_id,
                photo=photo_url,
                caption=caption,
                product_url=product_url,
            )
        except BaleAPIError as exc:
            log.error_message = str(exc)
            log.save(update_fields=("error_message", "updated_at"))
            raise CommandError(f"خطای بله: {exc}") from exc

        log.message_id = result.get("message_id")
        log.is_successful = True
        log.error_message = ""
        log.save(
            update_fields=(
                "message_id",
                "is_successful",
                "error_message",
                "updated_at",
            )
        )
        self.stdout.write(self.style.SUCCESS(f"ارسال شد: {product.name}"))
