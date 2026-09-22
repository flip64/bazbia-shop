from typing import Any

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class BasalamAPIError(Exception):
    """خطای کنترل‌شده ارتباط با API باسلام."""


class BasalamClient:
    def __init__(
        self,
        *,
        token: str | None = None,
        timeout: int = 20,
    ):
        self.base_url = settings.BASALAM_API_BASE_URL
        self.token = token or settings.BASALAM_ACCESS_TOKEN
        self.timeout = timeout
        self.session = requests.Session()

        if not self.token:
            raise ImproperlyConfigured(
                "متغیر BASALAM_ACCESS_TOKEN "
                "در فایل .env تنظیم نشده است."
            )

    def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"

        headers = kwargs.pop("headers", {})
        headers.update(
            {
                "Accept": "application/json",
                "Authorization": f"Bearer {self.token}",
            }
        )

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                timeout=self.timeout,
                **kwargs,
            )
        except requests.Timeout as exc:
            raise BasalamAPIError(
                "مهلت اتصال به باسلام تمام شد."
            ) from exc
        except requests.RequestException as exc:
            raise BasalamAPIError(
                "ارتباط با API باسلام برقرار نشد."
            ) from exc

        if not response.ok:
            try:
                error_data = response.json()
            except ValueError:
                error_data = response.text[:500]

            raise BasalamAPIError(
                f"خطای API باسلام "
                f"({response.status_code}): {error_data}"
            )

        try:
            return response.json()
        except ValueError as exc:
            raise BasalamAPIError(
                "پاسخ باسلام JSON معتبر نیست."
            ) from exc

    def get_current_user(self) -> dict[str, Any]:
        """دریافت اطلاعات حساب و غرفه متصل."""

        return self._request(
            "GET",
            "/v1/users/me",
        )

    def get_categories(self) -> dict[str, Any]:
        """دریافت ساختار درختی دسته‌بندی‌های باسلام."""

        return self._request(
            "GET",
            "/v1/categories",
        )

    def get_category(
        self,
        category_id: int,
    ) -> dict[str, Any]:
        """دریافت اطلاعات یک دسته خاص."""

        return self._request(
            "GET",
            f"/v1/categories/{category_id}",
        )

    def get_category_attributes(
        self,
        category_id: int,
    ) -> dict[str, Any]:
        """دریافت ویژگی‌های الزامی یک دسته."""

        return self._request(
            "GET",
            f"/v1/categories/{category_id}/attributes",
        )

    def upload_file(
        self,
        *,
        file_object,
        filename: str,
        content_type: str,
        file_type: str = "product.photo",
    ) -> dict[str, Any]:
        """آپلود فایل در باسلام."""

        return self._request(
            "POST",
            "/v1/files",
            files={
                "file": (
                    filename,
                    file_object,
                    content_type,
                )
            },
            data={
                "file_type": file_type,
            },
    )
