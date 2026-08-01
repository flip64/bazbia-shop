
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
