from dataclasses import dataclass

from django.db import transaction

from payments.models import Payment
from payments.services.gateways.zarinpal_gateway import (
    ZarinpalGateway,
    ZarinpalGatewayError,
)


@dataclass(frozen=True)
class ZarinpalCallbackResult:
    payment: Payment
    is_successful: bool
    message: str


class ZarinpalCallbackService:
    """
    بررسی بازگشت کاربر از زرین‌پال و تأیید واقعی تراکنش.
    """

    def __init__(
        self,
        *,
        payment: Payment,
        authority: str,
        callback_status: str,
    ):
        self.payment = payment
        self.authority = authority.strip()
        self.callback_status = (
            callback_status.strip().upper()
        )

    @transaction.atomic
    def run(self) -> ZarinpalCallbackResult:
        payment = (
            Payment.objects
            .select_for_update()
            .select_related("order")
            .get(pk=self.payment.pk)
        )

        if (
            payment.status ==
            Payment.Status.SUCCESSFUL
        ):
            return ZarinpalCallbackResult(
                payment=payment,
                is_successful=True,
                message=(
                    "این پرداخت قبلاً "
                    "با موفقیت تأیید شده است."
                ),
            )

        if payment.gateway != "zarinpal":
            raise ValueError(
                "این تراکنش متعلق به زرین‌پال نیست."
            )

        if (
            not payment.authority
            or payment.authority != self.authority
        ):
            raise ValueError(
                "شناسه Authority با تراکنش "
                "ثبت‌شده مطابقت ندارد."
            )

        if self.callback_status != "OK":
            payment.mark_cancelled(
                error_message=(
                    "پرداخت توسط کاربر لغو شد "
                    "یا در درگاه ناموفق بود."
                ),
                gateway_response={
                    "gateway": "zarinpal",
                    "authority": self.authority,
                    "callback_status":
                        self.callback_status,
                },
            )

            return ZarinpalCallbackResult(
                payment=payment,
                is_successful=False,
                message=(
                    "پرداخت لغو شد یا "
                    "ناموفق بود."
                ),
            )

        gateway = ZarinpalGateway()

        try:
            result = gateway.verify_payment(
                payment=payment,
                authority=self.authority,
            )

        except ZarinpalGatewayError as error:
            payment.mark_failed(
                error_message=str(error),
                gateway_response=(
                    error.response_data
                ),
            )

            raise ValueError(
                str(error)
            ) from error

        if not result.is_successful:
            payment.mark_failed(
                error_message=(
                    result.error_message
                ),
                gateway_response=(
                    result.raw_response
                ),
            )

            return ZarinpalCallbackResult(
                payment=payment,
                is_successful=False,
                message=(
                    result.error_message
                    or
                    "تأیید پرداخت ناموفق بود."
                ),
            )

        payment.mark_successful(
            tracking_code=(
                result.tracking_code
            ),
            reference_id=(
                result.reference_id
            ),
            gateway_response=(
                result.raw_response
            ),
        )

        return ZarinpalCallbackResult(
            payment=payment,
            is_successful=True,
            message=(
                "پرداخت با موفقیت "
                "تأیید شد."
            ),
        )
