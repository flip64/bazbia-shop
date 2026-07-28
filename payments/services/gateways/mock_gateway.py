# payments/services/gateways/mock_gateway.py

from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class PaymentRequestResult:
    """
    نتیجه ساخت درخواست پرداخت آزمایشی.
    """

    authority: str
    payment_url: str
    raw_response: dict


@dataclass(frozen=True)
class PaymentVerifyResult:
    """
    نتیجه بررسی و تأیید پرداخت آزمایشی.
    """

    is_successful: bool
    tracking_code: str
    reference_id: str
    raw_response: dict
    error_message: str = ""


class MockPaymentGateway:
    """
    درگاه پرداخت آزمایشی.

    این درگاه هیچ ارتباطی با بانک یا سرویس پرداخت واقعی
    ندارد و فقط برای آزمایش کامل جریان پرداخت استفاده می‌شود.

    وضعیت‌های قابل آزمایش:

    - success:
      پرداخت موفق

    - failed:
      پرداخت ناموفق

    - cancelled:
      لغو پرداخت توسط کاربر
    """

    gateway_code = "mock"

    def create_payment(
        self,
        payment,
        callback_url: str,
    ) -> PaymentRequestResult:
        """
        ساخت درخواست پرداخت آزمایشی.

        برای هر درخواست یک authority جدید ساخته می‌شود و
        آدرس callback همراه پارامترهای موردنیاز برگردانده
        خواهد شد.
        """

        authority = uuid4().hex

        separator = (
            "&"
            if "?" in callback_url
            else "?"
        )

        payment_url = (
            f"{callback_url}"
            f"{separator}"
            f"payment_id={payment.id}"
            f"&authority={authority}"
            f"&mock_status=success"
        )

        raw_response = {
            "gateway": self.gateway_code,
            "payment_id": payment.id,
            "order_id": payment.order_id,
            "amount": str(payment.amount),
            "authority": authority,
            "callback_url": callback_url,
            "payment_url": payment_url,
            "status": "created",
        }

        return PaymentRequestResult(
            authority=authority,
            payment_url=payment_url,
            raw_response=raw_response,
        )

    def verify_payment(
        self,
        payment,
        authority: str,
        mock_status: str,
    ) -> PaymentVerifyResult:
        """
        تأیید نتیجه پرداخت آزمایشی.

        authority دریافتی باید دقیقاً با authority ذخیره‌شده
        در رکورد Payment یکسان باشد.
        """

        normalized_authority = str(
            authority,
        ).strip()

        normalized_status = str(
            mock_status,
        ).strip().lower()

        # بررسی شناسه تراکنش
        if (
            not normalized_authority
            or normalized_authority
            != payment.authority
        ):
            return PaymentVerifyResult(
                is_successful=False,
                tracking_code="",
                reference_id="",
                error_message=(
                    "شناسه تراکنش با پرداخت ثبت‌شده "
                    "مطابقت ندارد."
                ),
                raw_response={
                    "gateway":
                        self.gateway_code,
                    "payment_id":
                        payment.id,
                    "order_id":
                        payment.order_id,
                    "authority":
                        normalized_authority,
                    "expected_authority":
                        payment.authority,
                    "status":
                        normalized_status,
                },
            )

        # پرداخت موفق
        if normalized_status == "success":
            tracking_code = (
                f"MOCK-"
                f"{uuid4().hex[:12].upper()}"
            )

            reference_id = (
                uuid4().hex[:16].upper()
            )

            return PaymentVerifyResult(
                is_successful=True,
                tracking_code=tracking_code,
                reference_id=reference_id,
                error_message="",
                raw_response={
                    "gateway":
                        self.gateway_code,
                    "payment_id":
                        payment.id,
                    "order_id":
                        payment.order_id,
                    "amount":
                        str(payment.amount),
                    "authority":
                        normalized_authority,
                    "status":
                        "success",
                    "tracking_code":
                        tracking_code,
                    "reference_id":
                        reference_id,
                },
            )

        # لغو توسط کاربر
        if normalized_status == "cancelled":
            return PaymentVerifyResult(
                is_successful=False,
                tracking_code="",
                reference_id="",
                error_message=(
                    "پرداخت توسط کاربر لغو شد."
                ),
                raw_response={
                    "gateway":
                        self.gateway_code,
                    "payment_id":
                        payment.id,
                    "order_id":
                        payment.order_id,
                    "authority":
                        normalized_authority,
                    "status":
                        "cancelled",
                },
            )

        # پرداخت ناموفق
        return PaymentVerifyResult(
            is_successful=False,
            tracking_code="",
            reference_id="",
            error_message=(
                "پرداخت ناموفق بود."
            ),
            raw_response={
                "gateway":
                    self.gateway_code,
                "payment_id":
                    payment.id,
                "order_id":
                    payment.order_id,
                "authority":
                    normalized_authority,
                "status":
                    "failed",
            },
        )
