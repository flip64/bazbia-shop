import random
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.utils import timezone

from customers.models import OTP


OTP_EXPIRE_MINUTES = 2
OTP_MAX_ATTEMPTS = 5


def generate_otp_code() -> str:
    """
    ساخت کد تأیید ۶ رقمی
    """
    return f"{random.randint(0, 999999):06d}"


@transaction.atomic
def create_otp(
    phone: str,
    purpose: str = OTP.Purpose.LOGIN,
) -> tuple[OTP, str]:
    """
    ساخت OTP جدید و باطل کردن OTPهای قبلی همان شماره و هدف.

    خروجی:
        otp: رکورد ساخته‌شده
        code: کد خام برای ارسال پیامک
    """

    OTP.objects.filter(
        phone=phone,
        purpose=purpose,
        is_used=False,
    ).update(is_used=True)

    code = generate_otp_code()

    otp = OTP.objects.create(
        phone=phone,
        purpose=purpose,
        code_hash=make_password(code),
        expires_at=timezone.now() + timedelta(
            minutes=OTP_EXPIRE_MINUTES
        ),
    )

    return otp, code


@transaction.atomic
def verify_otp(
    session_id,
    code: str,
) -> OTP:
    """
    بررسی کد OTP.

    در صورت درست بودن، OTP مصرف‌شده علامت‌گذاری می‌شود.
    در صورت خطا، ValueError ایجاد می‌شود.
    """

    try:
        otp = OTP.objects.select_for_update().get(
            session_id=session_id
        )
    except OTP.DoesNotExist:
        raise ValueError("درخواست کد تأیید پیدا نشد.")

    if otp.is_used:
        raise ValueError("این کد قبلاً استفاده شده است.")

    if timezone.now() >= otp.expires_at:
        raise ValueError("کد تأیید منقضی شده است.")

    if otp.attempts >= OTP_MAX_ATTEMPTS:
        raise ValueError("تعداد تلاش‌های مجاز به پایان رسیده است.")

    if not check_password(code, otp.code_hash):
        otp.attempts += 1
        otp.save(update_fields=["attempts"])

        remaining_attempts = OTP_MAX_ATTEMPTS - otp.attempts

        if remaining_attempts <= 0:
            raise ValueError("تعداد تلاش‌های مجاز به پایان رسیده است.")

        raise ValueError(
            f"کد تأیید نادرست است. "
            f"{remaining_attempts} تلاش باقی مانده است."
        )

    otp.is_used = True
    otp.verified_at = timezone.now()

    otp.save(
        update_fields=[
            "is_used",
            "verified_at",
        ]
    )

    return otp