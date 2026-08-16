import logging
import secrets

from datetime import timedelta

from django.contrib.auth.hashers import (
    check_password,
    make_password,
)
from django.db import transaction
from django.utils import timezone

from customers.models import OTP
from notifications.services.sms import send_otp_sms


logger = logging.getLogger(__name__)


OTP_EXPIRE_MINUTES = 2
OTP_MAX_ATTEMPTS = 5
OTP_REQUEST_COOLDOWN_SECONDS = 60


def generate_otp_code() -> str:
    """
    ساخت کد تأیید امن ۶ رقمی.
    """
    return f"{secrets.randbelow(1_000_000):06d}"


def mask_phone(phone: str) -> str:
    """
    مخفی‌کردن بخشی از شماره در لاگ.
    مثال: 0912***6789
    """
    phone = str(phone).strip()

    if len(phone) < 8:
        return "***"

    return f"{phone[:4]}***{phone[-4:]}"


def send_otp_notification(
    phone: str,
    code: str,
) -> None:
    """
    ارسال کد فقط از طریق پیامک.

    کد OTP و پاسخ کامل سرویس پیامک در لاگ ثبت نمی‌شود.
    """

    masked_phone = mask_phone(phone)

    try:
        send_otp_sms(
            phone=phone,
            code=code,
        )

        logger.info(
            "OTP SMS sent successfully. phone=%s",
            masked_phone,
        )

    except Exception:
        logger.exception(
            "OTP SMS sending failed. phone=%s",
            masked_phone,
        )


@transaction.atomic
def create_otp(
    phone: str,
    purpose: str = OTP.Purpose.LOGIN,
) -> tuple[OTP, str]:
    """
    ایجاد کد OTP جدید.

    توجه:
    مقدار code فقط برای ارسال پیامک برگردانده می‌شود
    و نباید در view، response یا log قرار بگیرد.
    """

    phone = str(phone).strip()

    if not phone:
        raise ValueError(
            "شماره موبایل الزامی است."
        )

    now = timezone.now()

    latest_otp = (
        OTP.objects
        .select_for_update()
        .filter(
            phone=phone,
            purpose=purpose,
        )
        .order_by("-created_at")
        .first()
    )

    if latest_otp:
        elapsed_seconds = (
            now - latest_otp.created_at
        ).total_seconds()

        if elapsed_seconds < OTP_REQUEST_COOLDOWN_SECONDS:
            remaining_seconds = max(
                1,
                int(
                    OTP_REQUEST_COOLDOWN_SECONDS
                    - elapsed_seconds
                ),
            )

            raise ValueError(
                f"لطفاً {remaining_seconds} ثانیه دیگر دوباره تلاش کنید."
            )

    OTP.objects.filter(
        phone=phone,
        purpose=purpose,
        is_used=False,
    ).update(
        is_used=True,
    )

    code = generate_otp_code()

    otp = OTP.objects.create(
        phone=phone,
        purpose=purpose,
        code_hash=make_password(code),
        expires_at=now + timedelta(
            minutes=OTP_EXPIRE_MINUTES,
        ),
        attempts=0,
        is_used=False,
    )

    transaction.on_commit(
        lambda: send_otp_notification(
            phone=phone,
            code=code,
        )
    )

    return otp, code


@transaction.atomic
def verify_otp(
    session_id,
    code: str,
) -> OTP:
    """
    بررسی کد OTP و مصرف آن در صورت موفقیت.
    """

    code = str(code).strip()

    if not code:
        raise ValueError(
            "کد تأیید الزامی است."
        )

    try:
        otp = (
            OTP.objects
            .select_for_update()
            .get(
                session_id=session_id,
            )
        )

    except OTP.DoesNotExist as exc:
        raise ValueError(
            "درخواست کد تأیید پیدا نشد."
        ) from exc

    if otp.is_used:
        raise ValueError(
            "این کد قبلاً استفاده شده است."
        )

    if timezone.now() >= otp.expires_at:
        otp.is_used = True
        otp.save(
            update_fields=[
                "is_used",
            ]
        )

        raise ValueError(
            "کد تأیید منقضی شده است."
        )

    if otp.attempts >= OTP_MAX_ATTEMPTS:
        otp.is_used = True
        otp.save(
            update_fields=[
                "is_used",
            ]
        )

        raise ValueError(
            "تعداد تلاش‌های مجاز به پایان رسیده است."
        )

    if not check_password(
        code,
        otp.code_hash,
    ):
        otp.attempts += 1

        remaining_attempts = (
            OTP_MAX_ATTEMPTS - otp.attempts
        )

        update_fields = [
            "attempts",
        ]

        if remaining_attempts <= 0:
            otp.is_used = True
            update_fields.append(
                "is_used"
            )

        otp.save(
            update_fields=update_fields,
        )

        if remaining_attempts <= 0:
            raise ValueError(
                "تعداد تلاش‌های مجاز به پایان رسیده است."
            )

        raise ValueError(
            f"کد تأیید نادرست است. "
            f"{remaining_attempts} تلاش دیگر باقی مانده است."
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
