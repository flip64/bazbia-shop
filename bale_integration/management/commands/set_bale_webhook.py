import re

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from bale_integration.services.bale_client import BaleAPIError, BaleClient


class Command(BaseCommand):
    help = (
        "وب‌هوک ربات بله را روی آدرس پروژه تنظیم می‌کند."
    )

    def handle(self, *args, **options):
        secret = settings.BALE_WEBHOOK_SECRET
        if not secret:
            raise CommandError("BALE_WEBHOOK_SECRET تنظیم نشده است.")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", secret):
            raise CommandError(
                "BALE_WEBHOOK_SECRET فقط می‌تواند شامل حروف، عدد، "
                "خط تیره و زیرخط باشد."
            )

        base_url = settings.BALE_BACKEND_URL.rstrip("/")
        if not base_url.startswith("https://"):
            raise CommandError("BALE_BACKEND_URL باید با https:// شروع شود.")
        webhook_url = f"{base_url}/api/bale/webhook/{secret}/"
        try:
            BaleClient().set_webhook(webhook_url)
        except BaleAPIError as exc:
            raise CommandError(
                f"تنظیم وب‌هوک بله ناموفق بود: {exc}"
            ) from exc

        self.stdout.write(
            self.style.SUCCESS(f"وب‌هوک بله تنظیم شد: {webhook_url}")
        )
