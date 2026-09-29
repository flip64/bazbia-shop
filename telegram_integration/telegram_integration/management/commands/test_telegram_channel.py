from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from telegram_integration.services import TelegramAPIError, TelegramClient


class Command(BaseCommand):
    help = "ارتباط ربات با کانال تلگرام را آزمایش می‌کند."

    def handle(self, *args, **options):
        channel_id = settings.TELEGRAM_CHANNEL_ID
        if not channel_id:
            raise CommandError("TELEGRAM_CHANNEL_ID تنظیم نشده است.")
        client = TelegramClient()
        try:
            chat = client.get_chat(channel_id)
            if chat.get("type") != "channel":
                raise CommandError(f"مقصد از نوع channel نیست: {chat.get('type')}")
            result = client.send_message(
                channel_id,
                "✅ اتصال Django بازبیا به کانال تلگرام برقرار است.",
            )
        except TelegramAPIError as exc:
            raise CommandError(f"خطای تلگرام: {exc}") from exc
        self.stdout.write(
            self.style.SUCCESS(f"پیام ارسال شد؛ message_id={result.get('message_id')}")
        )
