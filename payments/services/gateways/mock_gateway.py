from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class PaymentRequestResult:
    authority: str
    payment_url: str
    raw_response: dict


class MockPaymentGateway:
    """
    درگاه آزمایشی برای تست جریان پرداخت.
    """

    gateway_code = "mock"

    def create_payment(
        self,
        payment,
        callback_url: str,
    ) -> PaymentRequestResult:
        authority = uuid4().hex

        payment_url = (
            f"{callback_url}"
            f"?payment_id={payment.id}"
            f"&authority={authority}"
            f"&mock_status=success"
        )

        return PaymentRequestResult(
            authority=authority,
            payment_url=payment_url,
            raw_response={
                "gateway": self.gateway_code,
                "payment_id": payment.id,
                "order_id": payment.order_id,
                "amount": str(
                    payment.amount
                ),
                "authority": authority,
                "callback_url": callback_url,
            },
        )
