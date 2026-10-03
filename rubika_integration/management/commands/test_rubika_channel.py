from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from rubika_integration.services import RubikaAPIError, RubikaClient


class Command(BaseCommand):
    help = "اتصال ربات روبیکا به کانال را با یک پیام واقعی آزمایش می‌کند."

    def handle(self, *args, **options):
        channel_id = settings.RUBIKA_CHANNEL_ID
        if not channel_id:
            raise CommandError("RUBIKA_CHANNEL_ID تنظیم نشده است.")
        try:
            result = RubikaClient().send_message(
                channel_id,
                "✅ اتصال ربات بازبیا به کانال روبیکا برقرار است.",
            )
        except RubikaAPIError as exc:
            raise CommandError(f"خطای روبیکا: {exc}") from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"پیام آزمایشی روبیکا ارسال شد: {result.get('message_id', '-')}"
            )
        )
