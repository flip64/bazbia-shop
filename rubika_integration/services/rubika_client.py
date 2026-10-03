from io import BytesIO
from pathlib import PurePosixPath
from urllib.parse import urlparse

import requests
from django.conf import settings
from PIL import Image, ImageOps, UnidentifiedImageError


class RubikaAPIError(RuntimeError):
    """خطای ارتباط یا پاسخ ناموفق API روبیکا."""


class RubikaClient:
    API_ROOT = "https://botapi.rubika.ir/v3"

    def __init__(self, token=None, timeout=30):
        self.token = token or settings.RUBIKA_BOT_TOKEN
        self.timeout = timeout
        if not self.token:
            raise RubikaAPIError("RUBIKA_BOT_TOKEN تنظیم نشده است.")

    @staticmethod
    def _response_data(response):
        try:
            payload = response.json()
        except ValueError as exc:
            raise RubikaAPIError(
                f"پاسخ نامعتبر از روبیکا؛ HTTP {response.status_code}"
            ) from exc

        status = str(payload.get("status", "OK")).upper()
        if not response.ok or status not in {"OK", "SUCCESS"}:
            description = (
                payload.get("status_det")
                or payload.get("message")
                or payload.get("status")
                or "خطای نامشخص API روبیکا"
            )
            raise RubikaAPIError(description)
        return payload.get("data", payload)

    def _request(self, method, payload=None):
        try:
            response = requests.post(
                f"{self.API_ROOT}/{self.token}/{method}",
                json=payload or {},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise RubikaAPIError(f"ارتباط با روبیکا برقرار نشد: {exc}") from exc
        return self._response_data(response)

    def get_me(self):
        return self._request("getMe")

    def send_message(self, chat_id, text):
        return self._request(
            "sendMessage",
            {"chat_id": chat_id, "text": text},
        )

    @staticmethod
    def _normalize_image(image_content):
        """تصویر را به JPEG استاندارد و سازگار با sendFile روبیکا تبدیل می‌کند."""
        try:
            with Image.open(BytesIO(image_content)) as source:
                image = ImageOps.exif_transpose(source)
                if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
                    rgba = image.convert("RGBA")
                    background = Image.new("RGB", rgba.size, "white")
                    background.paste(rgba, mask=rgba.getchannel("A"))
                    image = background
                else:
                    image = image.convert("RGB")

                image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
                output = BytesIO()
                image.save(
                    output,
                    format="JPEG",
                    quality=90,
                    optimize=True,
                    progressive=False,
                )
                return output.getvalue()
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise RubikaAPIError("تصویر محصول معتبر نیست یا قابل تبدیل نیست.") from exc

    def _upload_image(self, photo_url):
        try:
            image_response = requests.get(photo_url, timeout=self.timeout)
        except requests.RequestException as exc:
            raise RubikaAPIError(f"دریافت تصویر محصول ناموفق بود: {exc}") from exc
        if not image_response.ok:
            raise RubikaAPIError(
                f"دریافت تصویر محصول ناموفق بود؛ HTTP {image_response.status_code}"
            )

        upload_request = self._request("requestSendFile", {"type": "Image"})
        upload_url = upload_request.get("upload_url")
        if not upload_url:
            raise RubikaAPIError("آدرس آپلود تصویر از روبیکا دریافت نشد.")

        original_filename = (
            PurePosixPath(urlparse(photo_url).path).name or "product.jpg"
        )
        filename = f"{PurePosixPath(original_filename).stem or 'product'}.jpg"
        image_content = self._normalize_image(image_response.content)
        content_type = "image/jpeg"
        try:
            upload_response = requests.post(
                upload_url,
                files={
                    "file": (
                        filename,
                        image_content,
                        content_type,
                    )
                },
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise RubikaAPIError(f"آپلود تصویر در روبیکا ناموفق بود: {exc}") from exc

        upload_data = self._response_data(upload_response)
        file_id = upload_data.get("file_id")
        if not file_id:
            raise RubikaAPIError("شناسه فایل آپلودشده از روبیکا دریافت نشد.")
        return file_id

    def send_product(self, chat_id, photo_url, caption, product_url):
        file_id = self._upload_image(photo_url)
        text = f"{caption}\n\n🛒 مشاهده و خرید محصول:\n{product_url}"
        return self._request(
            "sendFile",
            {
                "chat_id": chat_id,
                "file_id": file_id,
                "text": text,
            },
        )
