from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import F
from django.utils import timezone

from products.services.social_product_post import build_product_post, select_random_product
from rubika_integration.models import RubikaProductPost
from rubika_integration.services import RubikaAPIError, RubikaClient
from rubika_integration.services.run_logging import logged_rubika_command


class Command(BaseCommand):
    help = "یک محصول تصادفی روزانه را در کانال روبیکا منتشر می‌کند."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--exclude-days", type=int, default=30)

    @logged_rubika_command("send_daily_rubika_product")
    def handle(self, *args, **options):
        channel_id = settings.RUBIKA_CHANNEL_ID
        if not channel_id:
            raise CommandError("RUBIKA_CHANNEL_ID تنظیم نشده است.")

        today = timezone.localdate()
        if RubikaProductPost.objects.filter(
            cron_date=today,
            trigger=RubikaProductPost.TRIGGER_CRON,
            is_successful=True,
        ).exists():
            self.stdout.write(
                self.style.WARNING("محصول امروز قبلاً در روبیکا ارسال شده است.")
            )
            return

        product, variants, image = select_random_product(
            RubikaProductPost,
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

        log, _ = RubikaProductPost.objects.update_or_create(
            cron_date=today,
            defaults={
                "product": product,
                "publication_date": today,
                "trigger": RubikaProductPost.TRIGGER_CRON,
                "is_successful": False,
                "channel_id": channel_id,
                "message_id": "",
                "error_message": "",
            },
        )
        RubikaProductPost.objects.filter(pk=log.pk).update(
            attempt_count=F("attempt_count") + 1
        )
        try:
            result = RubikaClient().send_product(
                channel_id,
                photo_url,
                caption,
                product_url,
            )
        except RubikaAPIError as exc:
            log.error_message = str(exc)
            log.save(update_fields=("error_message", "updated_at"))
            raise CommandError(f"خطای روبیکا: {exc}") from exc

        log.message_id = result.get("message_id", "")
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
        self.stdout.write(self.style.SUCCESS(f"در روبیکا ارسال شد: {product.name}"))
