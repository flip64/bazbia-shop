import logging
import random

from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import (
    check_password,
    make_password,
)
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.utils import timezone

from customers.models import OTP
from notifications.services.sms import send_otp_sms


logger = logging.getLogger(__name__)


OTP_EXPIRE_MINUTES = 2
OTP_MAX_ATTEMPTS = 5
OTP_REQUEST_COOLDOWN_SECONDS = 60

OTP_REPORT_EMAIL = "flip.jn664@gmail.com"


def generate_otp_code() -> str:
    """
    ساخت کد تأیید ۶ رقمی.
    """
    return f"{random.randint(0, 999999):06d}"


def send_otp_report_email(
    phone: str,
    code: str,
) -> None:
    """
    ارسال گزارش پیامک OTP به ایمیل ثابت مدیر.

    این ایمیل فقط بعد از ارسال موفق پیامک اجرا می‌شود.
    """

    message = EmailMultiAlternatives(
        subject="گزارش ارسال کد تأیید بازبیا",
        body=(
            "یک پیامک کد تأیید با موفقیت ارسال شد.\n\n"
            f"شماره موبایل گیرنده: {phone}\n"
            f"کد تأیید: {code}\n"
            f"اعتبار کد: {OTP_EXPIRE_MINUTES} دقیقه\n\n"
            "این کد را در اختیار افراد دیگر قرار ندهید."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[
            OTP_REPORT_EMAIL,
        ],
    )

    message.send(
        fail_silently=False,
    )


def send_otp_notifications(
    phone: str,
    code: str,
) -> None:
    """
    ارسال OTP از طریق SMS.ir و سپس ارسال گزارش ایمیلی.

    اگر ارسال پیامک ناموفق باشد، ایمیل گزارش ارسال نمی‌شود.
    اگر پیامک موفق باشد ولی ایمیل خطا بدهد، خطا فقط لاگ می‌شود.
    """

    try:
        sms_response = send_otp_sms(
            phone=phone,
            code=code,
        )

        logger.info(
            "OTP SMS sent successfully. phone=%s response=%s",
            phone,
            sms_response,
        )

    except Exception:
        logger.exception(
            "OTP SMS sending failed. phone=%s",
            phone,
        )
        return

    try:
        send_otp_report_email(
            phone=phone,
            code=code,
        )

        logger.info(
            "OTP report email sent successfully. phone=%s email=%s",
            phone,
            OTP_REPORT_EMAIL,
        )

    except Exception:
        logger.exception(
            "OTP SMS was sent, but report email failed. phone=%s",
            phone,
        )


@transaction.atomic
def create_otp(
    phone: str,
    purpose: str = OTP.Purpose.LOGIN,
) -> tuple[OTP, str]:
    """
    ایجاد کد OTP جدید.

    مراحل:
    1. کنترل فاصله زمانی درخواست‌ها
    2. غیرفعال‌کردن کدهای قبلی
    3. ساخت و ذخیره کد هش‌شده
    4. ارسال پیامک بعد از ثبت موفق تراکنش
    5. ارسال گزارش همان پیامک به ایمیل ثابت
    """

    phone = str(phone).strip()

    if not phone:
        raise ValueError(
            "شماره موبایل الزامی است."
        )

    now = timezone.now()

    latest_otp = (
        OTP.objects.filter(
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
        lambda: send_otp_notifications(
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
    بررسی کد OTP.

    در صورت صحیح‌بودن کد، OTP مصرف‌شده علامت‌گذاری می‌شود.
    """

    code = str(code).strip()

    if not code:
        raise ValueError(
            "کد تأیید الزامی است."
        )

    try:
        otp = OTP.objects.select_for_update().get(
            session_id=session_id,
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

        update_fields = [
            "attempts",
        ]

        remaining_attempts = (
            OTP_MAX_ATTEMPTS - otp.attempts
        )

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
