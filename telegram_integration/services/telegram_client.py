import requests
from django.conf import settings


class TelegramAPIError(RuntimeError):
    """خطای ارتباط یا پاسخ ناموفق API تلگرام."""


class TelegramClient:
    API_ROOT = "https://api.telegram.org"

    def __init__(self, token=None, timeout=30):
        self.token = token or settings.TELEGRAM_BOT_TOKEN
        self.timeout = timeout
        if not self.token:
            raise TelegramAPIError("TELEGRAM_BOT_TOKEN تنظیم نشده است.")

    def _request(self, method, payload):
        try:
            response = requests.post(
                f"{self.API_ROOT}/bot{self.token}/{method}",
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise TelegramAPIError(f"ارتباط با تلگرام برقرار نشد: {exc}") from exc
        try:
            data = response.json()
        except ValueError as exc:
            raise TelegramAPIError(
                f"پاسخ نامعتبر از تلگرام؛ HTTP {response.status_code}"
            ) from exc
        if not response.ok or not data.get("ok"):
            raise TelegramAPIError(data.get("description", "خطای نامشخص API تلگرام"))
        return data["result"]

    def get_chat(self, chat_id):
        return self._request("getChat", {"chat_id": chat_id})

    def send_message(self, chat_id, text):
        return self._request("sendMessage", {"chat_id": chat_id, "text": text})

    def send_photo(self, chat_id, photo, caption, product_url):
        return self._request(
            "sendPhoto",
            {
                "chat_id": chat_id,
                "photo": photo,
                "caption": caption,
                "reply_markup": {
                    "inline_keyboard": [[{
                        "text": "مشاهده و خرید محصول",
                        "url": product_url,
                    }]],
                },
            },
        )
