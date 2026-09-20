import requests
from django.conf import settings


class BaleAPIError(RuntimeError):
    """خطای ارتباط یا پاسخ ناموفق API بله."""


class BaleClient:
    API_ROOT = "https://tapi.bale.ai"

    def __init__(self, token=None, timeout=30):
        self.token = token or settings.BALE_BOT_TOKEN
        self.timeout = timeout
        if not self.token:
            raise BaleAPIError("BALE_BOT_TOKEN تنظیم نشده است.")

    def _request(self, method, payload):
        try:
            response = requests.post(
                f"{self.API_ROOT}/bot{self.token}/{method}",
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise BaleAPIError(f"ارتباط با بله برقرار نشد: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise BaleAPIError(
                f"پاسخ نامعتبر از بله؛ HTTP {response.status_code}"
            ) from exc

        if not response.ok or not data.get("ok"):
            raise BaleAPIError(data.get("description", "خطای نامشخص API بله"))
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
                    "inline_keyboard": [[
                        {
                            "text": "مشاهده و خرید محصول",
                            "url": product_url,
                        }
                    ]]
                },
            },
        )
