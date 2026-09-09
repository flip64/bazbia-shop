from django.conf import settings

from .sms_ir import SMSIRService


def send_otp_sms(
    phone: str,
    code: str,
) -> dict:
    """
    ارسال پیامک OTP.
    """

    service = SMSIRService()

    return service.send_otp(
        phone=phone,
        code=code,
    )


def send_paid_order_sms(
    *,
    phone: str,
    customer_name: str,
    order_id: int,
) -> dict:
    """
    ارسال پیامک تأیید سفارش پرداخت‌شده.
    """

    template_id = getattr(
        settings,
        "SMS_IR_PAID_ORDER_TEMPLATE_ID",
        0,
    )

    if not template_id:
        raise ValueError(
            "SMS_IR_PAID_ORDER_TEMPLATE_ID تنظیم نشده است."
        )

    customer_name_parameter = getattr(
        settings,
        "SMS_IR_CUSTOMER_NAME_PARAMETER",
        "CUSTOMER_NAME",
    )

    order_id_parameter = getattr(
        settings,
        "SMS_IR_ORDER_ID_PARAMETER",
        "ORDER_ID",
    )

    service = SMSIRService()

    return service.send_template(
        phone=phone,
        template_id=template_id,
        parameters={
            customer_name_parameter: customer_name,
            order_id_parameter: str(order_id),
        },
    )
