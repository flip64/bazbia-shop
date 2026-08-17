from .sms_ir import SMSIRService


def send_otp_sms(
    phone: str,
    code: str,
) -> dict:
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
    from django.conf import settings

    service = SMSIRService()

    return service.send_template(
        phone=phone,
        template_id=(
            settings.SMS_IR_PAID_ORDER_TEMPLATE_ID
        ),
        parameters={
            settings.SMS_IR_CUSTOMER_NAME_PARAMETER:
                customer_name,

            settings.SMS_IR_ORDER_ID_PARAMETER:
                order_id,
        },
    )
