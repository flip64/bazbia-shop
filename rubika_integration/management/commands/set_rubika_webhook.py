import re

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from rubika_integration.services import RubikaAPIError, RubikaClient
from rubika_integration.services.run_logging import logged_rubika_command


class Command(BaseCommand):
    help = "وب‌هوک و فهرست فرمان‌های ربات روبیکا را تنظیم می‌کند."

    @logged_rubika_command("set_rubika_webhook")
    def handle(self, *args, **options):
        secret = settings.RUBIKA_WEBHOOK_SECRET
        if not secret:
            raise CommandError("RUBIKA_WEBHOOK_SECRET تنظیم نشده است.")
        if not re.fullmatch(r"[A-Za-z0-9_-]{24,}", secret):
            raise CommandError(
                "RUBIKA_WEBHOOK_SECRET باید حداقل ۲۴ کاراکتر و فقط شامل "
                "حروف، عدد، خط تیره و زیرخط باشد."
            )

        base_url = settings.RUBIKA_BACKEND_URL.rstrip("/")
        if not base_url.startswith("https://"):
            raise CommandError("RUBIKA_BACKEND_URL باید با https:// شروع شود.")

        webhook_url = f"{base_url}/api/rubika/webhook/{secret}/"
        commands = [
            {"command": "start", "description": "نمایش راهنمای ربات"},
            {"command": "random", "description": "ارسال محصول تصادفی"},
            {"command": "product", "description": "ارسال محصول با شناسه"},
            {"command": "id", "description": "نمایش شناسه کاربری"},
        ]
        try:
            client = RubikaClient()
            client.update_endpoint(webhook_url, "ReceiveUpdate")
            client.set_commands(commands)
        except RubikaAPIError as exc:
            raise CommandError(f"تنظیم وب‌هوک روبیکا ناموفق بود: {exc}") from exc

        self.stdout.write(self.style.SUCCESS("وب‌هوک و فرمان‌های روبیکا تنظیم شدند."))
