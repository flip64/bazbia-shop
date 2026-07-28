from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction

from orders.models import Order
from payments.models import Payment
from payments.services.gateways.mock_gateway import (
    MockPaymentGateway,
)


@dataclass(frozen=True)
class PaymentCreateResult:
    """
    نتیجه ساخت درخواست پرداخت.
    """

    payment: Payment
    payment_url: str


class PaymentCreateService:
    """
    مسئول ساخت تراکنش پرداخت برای یک سفارش.

    این سرویس:
    - مالکیت سفارش را بررسی نمی‌کند؛ View انجام می‌دهد.
    - مبلغ را فقط از خود سفارش می‌خواند.
    - از ساخت پرداخت برای سفارش پرداخت‌شده جلوگیری می‌کند.
    """

    def __init__(
        self,
        order: Order,
        callback_url: str,
    ):
        self.order = order
        self.callback_url = callback_url

    @transaction.atomic
    def run(self) -> PaymentCreateResult:
        order = (
            Order.objects
            .select_for_update()
            .get(pk=self.order.pk)
        )

        if order.status == Order.STATUS_PAID:
            raise ValueError(
                "این سفارش قبلاً پرداخت شده است."
            )

        if order.status == Order.STATUS_CANCELLED:
            raise ValueError(
                "سفارش لغوشده قابل پرداخت نیست."
            )

        amount = Decimal(
            str(order.total_price)
        )

        if amount <= 0:
            raise ValueError(
                "مبلغ سفارش معتبر نیست."
            )

        pending_payment = (
            Payment.objects
            .filter(
                order=order,
                status__in=[
                    Payment.Status.PENDING,
                    Payment.Status.PROCESSING,
                ],
            )
            .order_by("-created_at")
            .first()
        )

        if pending_payment:
            payment = pending_payment
        else:
            payment = Payment.objects.create(
                order=order,
                amount=amount,
                payment_method=(
                    Payment.Method.ONLINE
                ),
                status=Payment.Status.PENDING,
                gateway="mock",
            )

        gateway = MockPaymentGateway()

        gateway_result = gateway.create_payment(
            payment=payment,
            callback_url=self.callback_url,
        )

        payment.authority = (
            gateway_result.authority
        )

        payment.gateway_response = (
            gateway_result.raw_response
        )

        payment.status = (
            Payment.Status.PROCESSING
        )

        payment.save(
            update_fields=[
                "authority",
                "gateway_response",
                "status",
                "updated_at",
            ],
        )

        return PaymentCreateResult(
            payment=payment,
            payment_url=(
                gateway_result.payment_url
            ),
        )
