from dataclasses import dataclass
from typing import Any

import requests

from django.conf import settings


@dataclass(frozen=True)
class ZarinpalRequestResult:
    """
    نتیجه درخواست ایجاد پرداخت در زرین‌پال.
    """

    authority: str
    payment_url: str
    raw_response: dict[str, Any]


@dataclass(frozen=True)
class ZarinpalVerifyResult:
    """
    نتیجه تأیید تراکنش زرین‌پال.
    """

    is_successful: bool
    code: int
    reference_id: str
    tracking_code: str
    raw_response: dict[str, Any]
    error_message: str = ""


class ZarinpalGatewayError(Exception):
    """
    خطای ارتباط یا پاسخ نامعتبر زرین‌پال.
    """

    def __init__(
        self,
        message: str,
        *,
        code: int | None = None,
        response_data: dict[str, Any] | None = None,
    ):
        super().__init__(message)

        self.code = code
        self.response_data = response_data or {}


class ZarinpalGateway:
    """
    اتصال مستقیم به API نسخه ۴ زرین‌پال.
    """

    gateway_code = "zarinpal"

    request_url = (
        "https://payment.zarinpal.com/"
        "pg/v4/payment/request.json"
    )

    verify_url = (
        "https://payment.zarinpal.com/"
        "pg/v4/payment/verify.json"
    )

    start_pay_url = (
        "https://payment.zarinpal.com/"
        "pg/StartPay/{authority}"
    )

    timeout_seconds = 20

    def __init__(self):
        self.merchant_id = (
            settings.ZARINPAL_MERCHANT_ID
        )

        self.currency = (
            settings.ZARINPAL_CURRENCY
        )

        self._validate_settings()

    def _validate_settings(self) -> None:
        """
        اعتبارسنجی تنظیمات ضروری درگاه.
        """

        if not self.merchant_id:
            raise ZarinpalGatewayError(
                "شناسه پذیرنده زرین‌پال "
                "در تنظیمات سرور وارد نشده است."
            )

        if self.currency not in {
            "IRT",
            "IRR",
        }:
            raise ZarinpalGatewayError(
                "واحد پول زرین‌پال باید "
                "IRT یا IRR باشد."
            )

    def create_payment(
        self,
        payment,
        callback_url: str,
    ) -> ZarinpalRequestResult:
        """
        ایجاد درخواست پرداخت واقعی در زرین‌پال.
        """

        amount = self._normalize_amount(
            payment.amount
        )

        payload = {
            "merchant_id":
                self.merchant_id,

            "currency":
                self.currency,

            "amount":
                amount,

            "description": (
                "پرداخت سفارش "
                f"شماره {payment.order_id} "
                "فروشگاه بازبیا"
            ),

            "callback_url":
                callback_url,

            "metadata": {
                "order_id":
                    str(payment.order_id),

                "payment_id":
                    str(payment.id),
            },
        }

        response_data = self._post_json(
            url=self.request_url,
            payload=payload,
        )

        data = response_data.get(
            "data",
        ) or {}

        code = self._to_int(
            data.get("code"),
        )

        authority = str(
            data.get("authority") or "",
        ).strip()

        if code != 100 or not authority:
            raise ZarinpalGatewayError(
                self._extract_error_message(
                    response_data,
                    default=(
                        "زرین‌پال درخواست پرداخت "
                        "را نپذیرفت."
                    ),
                ),
                code=code,
                response_data=response_data,
            )

        payment_url = (
            self.start_pay_url.format(
                authority=authority,
            )
        )

        return ZarinpalRequestResult(
            authority=authority,
            payment_url=payment_url,
            raw_response=response_data,
        )

    def verify_payment(
        self,
        payment,
        authority: str,
    ) -> ZarinpalVerifyResult:
        """
        تأیید نهایی تراکنش با API زرین‌پال.
        """

        normalized_authority = str(
            authority,
        ).strip()

        if not normalized_authority:
            return ZarinpalVerifyResult(
                is_successful=False,
                code=-1,
                reference_id="",
                tracking_code="",
                error_message=(
                    "شناسه Authority ارسال نشده است."
                ),
                raw_response={},
            )

        if (
            payment.authority
            and payment.authority
            != normalized_authority
        ):
            return ZarinpalVerifyResult(
                is_successful=False,
                code=-2,
                reference_id="",
                tracking_code="",
                error_message=(
                    "شناسه تراکنش با پرداخت "
                    "ثبت‌شده مطابقت ندارد."
                ),
                raw_response={
                    "authority":
                        normalized_authority,

                    "expected_authority":
                        payment.authority,
                },
            )

        payload = {
            "merchant_id":
                self.merchant_id,

            "amount":
                self._normalize_amount(
                    payment.amount
                ),

            "authority":
                normalized_authority,
        }

        response_data = self._post_json(
            url=self.verify_url,
            payload=payload,
        )

        data = response_data.get(
            "data",
        ) or {}

        code = self._to_int(
            data.get("code"),
        )

        reference_id = str(
            data.get("ref_id") or "",
        ).strip()

        # 100: تأیید موفق
        # 101: قبلاً تأیید شده
        is_successful = code in {
            100,
            101,
        }

        if is_successful:
            return ZarinpalVerifyResult(
                is_successful=True,
                code=code,
                reference_id=reference_id,
                tracking_code=reference_id,
                error_message="",
                raw_response=response_data,
            )

        return ZarinpalVerifyResult(
            is_successful=False,
            code=code,
            reference_id="",
            tracking_code="",
            error_message=(
                self._extract_error_message(
                    response_data,
                    default=(
                        "تأیید پرداخت زرین‌پال "
                        "ناموفق بود."
                    ),
                )
            ),
            raw_response=response_data,
        )

    def _post_json(
        self,
        *,
        url: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        ارسال امن درخواست JSON به زرین‌پال.
        """

        try:
            response = requests.post(
                url,
                json=payload,
                headers={
                    "Accept":
                        "application/json",

                    "Content-Type":
                        "application/json",
                },
                timeout=self.timeout_seconds,
            )

            response.raise_for_status()

        except requests.Timeout as error:
            raise ZarinpalGatewayError(
                "زمان پاسخ‌گویی زرین‌پال "
                "به پایان رسید."
            ) from error

        except requests.RequestException as error:
            raise ZarinpalGatewayError(
                "ارتباط با زرین‌پال "
                "برقرار نشد."
            ) from error

        try:
            data = response.json()
        except ValueError as error:
            raise ZarinpalGatewayError(
                "پاسخ زرین‌پال JSON معتبر نیست."
            ) from error

        if not isinstance(data, dict):
            raise ZarinpalGatewayError(
                "ساختار پاسخ زرین‌پال "
                "معتبر نیست."
            )

        return data

    def _normalize_amount(
        self,
        amount,
    ) -> int:
        """
        تبدیل Decimal یا رشته مبلغ به عدد صحیح.
        """

        normalized_amount = int(
            round(float(amount))
        )

        if normalized_amount <= 0:
            raise ZarinpalGatewayError(
                "مبلغ پرداخت معتبر نیست."
            )

        return normalized_amount

    @staticmethod
    def _to_int(
        value: Any,
    ) -> int:
        try:
            return int(value)
        except (
            TypeError,
            ValueError,
        ):
            return 0

    @staticmethod
    def _extract_error_message(
        response_data: dict[str, Any],
        *,
        default: str,
    ) -> str:
        errors = response_data.get(
            "errors",
        )

        if isinstance(errors, dict):
            message = str(
                errors.get("message") or "",
            ).strip()

            if message:
                return message

        if isinstance(errors, list):
            for item in errors:
                if isinstance(item, dict):
                    message = str(
                        item.get("message") or "",
                    ).strip()

                    if message:
                        return message

        data = response_data.get(
            "data",
        )

        if isinstance(data, dict):
            message = str(
                data.get("message") or "",
            ).strip()

            if message:
                return message

        return default
