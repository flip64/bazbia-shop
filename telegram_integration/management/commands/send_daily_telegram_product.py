from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import F
from django.utils import timezone

from products.services.social_product_post import build_product_post, select_random_product
from telegram_integration.models import TelegramProductPost
from telegram_integration.services import TelegramAPIError, TelegramClient


class Command(BaseCommand):
    help = "یک محصول تصادفی را با محدودیت زمانی در کانال تلگرام منتشر می‌کند."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--exclude-days", type=int, default=30)

    def handle(self, *args, **options):
        channel_id = settings.TELEGRAM_CHANNEL_ID
        if not channel_id:
            raise CommandError("TELEGRAM_CHANNEL_ID تنظیم نشده است.")
        today = timezone.localdate()
        if TelegramProductPost.objects.filter(
            cron_date=today,
            trigger=TelegramProductPost.TRIGGER_CRON,
            is_successful=True,
        ).exists():
            self.stdout.write(self.style.WARNING("محصول امروز قبلاً در تلگرام ارسال شده است."))
            return

        product, variants, image = select_random_product(
            TelegramProductPost,
            exclude_days=options["exclude_days"],
        )
        if product is None:
            raise CommandError("محصول فعال، موجود و دارای تصویر پیدا نشد.")
        photo_url, caption, product_url = build_product_post(product, variants, image)
        if options["dry_run"]:
            self.stdout.write(f"Product: {product.name}")
            self.stdout.write(f"Photo: {photo_url}")
            self.stdout.write(f"URL: {product_url}")
            self.stdout.write("--- Caption ---")
            self.stdout.write(caption)
            return

        log, _ = TelegramProductPost.objects.update_or_create(
            cron_date=today,
            defaults={
                "product": product,
                "publication_date": today,
                "trigger": TelegramProductPost.TRIGGER_CRON,
                "is_successful": False,
                "channel_id": channel_id,
                "message_id": None,
                "error_message": "",
            },
        )
        TelegramProductPost.objects.filter(pk=log.pk).update(
            attempt_count=F("attempt_count") + 1
        )
        try:
            result = TelegramClient().send_photo(channel_id, photo_url, caption, product_url)
        except TelegramAPIError as exc:
            log.error_message = str(exc)
            log.save(update_fields=("error_message", "updated_at"))
            raise CommandError(f"خطای تلگرام: {exc}") from exc
        log.message_id = result.get("message_id")
        log.is_successful = True
        log.error_message = ""
        log.save(update_fields=("message_id", "is_successful", "error_message", "updated_at"))
        self.stdout.write(self.style.SUCCESS(f"در تلگرام ارسال شد: {product.name}"))
