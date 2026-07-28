from dataclasses import dataclass

from django.db import transaction

from orders.models import Order
from payments.models import Payment
from payments.services.gateways.mock_gateway import (
    MockPaymentGateway,
)


@dataclass(frozen=True)
class PaymentVerifyResult:
    payment: Payment
    message: str


class PaymentVerifyService:
    """
    تأیید نتیجه پرداخت و بروزرسانی وضعیت تراکنش و سفارش.
    """

    def __init__(
        self,
        payment: Payment,
        authority: str,
        mock_status: str,
    ):
        self.payment = payment
        self.authority = authority
        self.mock_status = mock_status

    @transaction.atomic
    def run(self) -> PaymentVerifyResult:
        payment = (
            Payment.objects
            .select_for_update()
            .select_related("order")
            .get(pk=self.payment.pk)
        )

        if payment.status == Payment.Status.SUCCESSFUL:
            return PaymentVerifyResult(
                payment=payment,
                message="این پرداخت قبلاً تأیید شده است.",
            )

        gateway = MockPaymentGateway()

        result = gateway.verify_payment(
            payment=payment,
            authority=self.authority,
            mock_status=self.mock_status,
        )

        if result.is_successful:
            payment.mark_successful(
                tracking_code=result.tracking_code,
                reference_id=result.reference_id,
                gateway_response=result.raw_response,
            )

            return PaymentVerifyResult(
                payment=payment,
                message="پرداخت با موفقیت تأیید شد.",
            )

        if self.mock_status == "cancelled":
            payment.mark_cancelled(
                error_message=result.error_message,
                gateway_response=result.raw_response,
            )
        else:
            payment.mark_failed(
                error_message=result.error_message,
                gateway_response=result.raw_response,
            )

        return PaymentVerifyResult(
            payment=payment,
            message=result.error_message,
        )
