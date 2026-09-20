from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from bale_integration.services.bale_client import BaleAPIError, BaleClient


class Command(BaseCommand):
    help = "ارتباط بازو با کانال بله را آزمایش می‌کند."

    def handle(self, *args, **options):
        channel_id = settings.BALE_CHANNEL_ID
        if not channel_id:
            raise CommandError("BALE_CHANNEL_ID تنظیم نشده است.")

        client = BaleClient()
        try:
            chat = client.get_chat(channel_id)
            if chat.get("type") != "channel":
                raise CommandError(
                    f"مقصد از نوع channel نیست: {chat.get('type')}"
                )
            result = client.send_message(
                channel_id,
                "✅ اتصال Django بازبیا به کانال بله برقرار است.",
            )
        except BaleAPIError as exc:
            raise CommandError(f"خطای بله: {exc}") from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"پیام ارسال شد؛ message_id={result.get('message_id')}"
            )
        )
