from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction

from orders.models import Order
from payments.models import Payment
from payments.services.gateways import (
    ZarinpalGatewayError,
    get_payment_gateway,
)


@dataclass(frozen=True)
class PaymentCreateResult:
    """
    نتیجه ایجاد درخواست پرداخت.
    """

    payment: Payment
    payment_url: str


class PaymentCreateService:
    """
    ساخت درخواست پرداخت برای یک سفارش.

    وظایف:
    - قفل‌کردن سفارش هنگام ایجاد پرداخت
    - بررسی وضعیت سفارش
    - تعیین مبلغ از دیتابیس
    - انتخاب درگاه از Gateway Factory
    - ذخیره Authority و پاسخ درگاه
    """

    def __init__(
        self,
        order: Order,
        callback_url: str,
    ):
        self.order = order
        self.callback_url = (
            callback_url.strip()
        )

    @transaction.atomic
    def run(self) -> PaymentCreateResult:
        order = (
            Order.objects
            .select_for_update()
            .get(pk=self.order.pk)
        )

        self._validate_order(order)

        amount = Decimal(
            str(order.total_price)
        )

        if amount <= 0:
            raise ValueError(
                "مبلغ سفارش معتبر نیست."
            )

        if not self.callback_url:
            raise ValueError(
                "آدرس بازگشت پرداخت تعریف نشده است."
            )

        gateway = get_payment_gateway()

        gateway_code = str(
            gateway.gateway_code
        ).strip()

        payment = self._get_or_create_payment(
            order=order,
            amount=amount,
            gateway_code=gateway_code,
        )

        try:
            gateway_result = (
                gateway.create_payment(
                    payment=payment,
                    callback_url=(
                        self.callback_url
                    ),
                )
            )

        except ZarinpalGatewayError as error:
            payment.status = (
                Payment.Status.FAILED
            )

            payment.error_message = str(
                error
            )

            payment.gateway_response = (
                error.response_data
            )

            payment.save(
                update_fields=[
                    "status",
                    "error_message",
                    "gateway_response",
                    "updated_at",
                ]
            )

            raise ValueError(
                str(error)
            ) from error

        except Exception as error:
            payment.status = (
                Payment.Status.FAILED
            )

            payment.error_message = (
                "ایجاد درخواست پرداخت "
                "با خطا مواجه شد."
            )

            payment.save(
                update_fields=[
                    "status",
                    "error_message",
                    "updated_at",
                ]
            )

            raise ValueError(
                "ارتباط با درگاه پرداخت "
                "با خطا مواجه شد."
            ) from error

        payment.gateway = gateway_code

        payment.authority = (
            gateway_result.authority
        )

        payment.gateway_response = (
            gateway_result.raw_response
        )

        payment.error_message = ""

        payment.status = (
            Payment.Status.PROCESSING
        )

        payment.save(
            update_fields=[
                "gateway",
                "authority",
                "gateway_response",
                "error_message",
                "status",
                "updated_at",
            ]
        )

        return PaymentCreateResult(
            payment=payment,
            payment_url=(
                gateway_result.payment_url
            ),
        )

    def _validate_order(
        self,
        order: Order,
    ) -> None:
        """
        بررسی امکان پرداخت سفارش.
        """

        if order.status == "paid":
            raise ValueError(
                "این سفارش قبلاً پرداخت شده است."
            )

        if order.status == "cancelled":
            raise ValueError(
                "سفارش لغوشده قابل پرداخت نیست."
            )

        if order.payment_method != "online":
            raise ValueError(
                "روش پرداخت این سفارش آنلاین نیست."
            )

    def _get_or_create_payment(
        self,
        *,
        order: Order,
        amount: Decimal,
        gateway_code: str,
    ) -> Payment:
        """
        دریافت پرداخت فعال یا ساخت یک پرداخت جدید.

        برای جلوگیری از ساخت چند تراکنش هم‌زمان، آخرین
        پرداخت pending یا processing همان سفارش استفاده
        می‌شود.
        """

        payment = (
            Payment.objects
            .select_for_update()
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

        if payment is None:
            return Payment.objects.create(
                order=order,
                amount=amount,
                payment_method=(
                    Payment.Method.ONLINE
                ),
                status=(
                    Payment.Status.PENDING
                ),
                gateway=gateway_code,
            )

        changed_fields = []

        if payment.amount != amount:
            payment.amount = amount
            changed_fields.append(
                "amount"
            )

        if payment.gateway != gateway_code:
            payment.gateway = gateway_code
            changed_fields.append(
                "gateway"
            )

        if payment.status != Payment.Status.PENDING:
            payment.status = (
                Payment.Status.PENDING
            )
            changed_fields.append(
                "status"
            )

        if payment.error_message:
            payment.error_message = ""
            changed_fields.append(
                "error_message"
            )

        if changed_fields:
            changed_fields.append(
                "updated_at"
            )

            payment.save(
                update_fields=changed_fields
            )

        return payment
