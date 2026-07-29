from django.conf import settings

from payments.services.gateways.mock_gateway import (
    MockPaymentGateway,
)
from payments.services.gateways.zarinpal_gateway import (
    ZarinpalGateway,
)


class UnsupportedPaymentGatewayError(
    ValueError
):
    """
    زمانی ایجاد می‌شود که نام درگاه تعریف‌شده
    در تنظیمات پشتیبانی نشود.
    """


def get_payment_gateway():
    """
    ساخت درگاه پرداخت براساس PAYMENT_GATEWAY.

    مقادیر پشتیبانی‌شده:
    - mock
    - zarinpal
    """

    gateway_name = str(
        getattr(
            settings,
            "PAYMENT_GATEWAY",
            "mock",
        )
    ).strip().lower()

    gateways = {
        "mock": MockPaymentGateway,
        "zarinpal": ZarinpalGateway,
    }

    gateway_class = gateways.get(
        gateway_name,
    )

    if gateway_class is None:
        raise UnsupportedPaymentGatewayError(
            (
                "درگاه پرداخت "
                f"«{gateway_name}» "
                "پشتیبانی نمی‌شود."
            )
        )

    return gateway_class()
