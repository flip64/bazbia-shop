# customers/validators.py

import re

from django.core.exceptions import ValidationError


IRANIAN_PHONE_PATTERN = re.compile(r"^09\d{9}$")
OTP_CODE_PATTERN = re.compile(r"^\d{6}$")


def normalize_phone(phone: str) -> str:
    phone = str(phone).strip()

    phone = (
        phone
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    if phone.startswith("+98"):
        phone = "0" + phone[3:]

    elif phone.startswith("0098"):
        phone = "0" + phone[4:]

    elif phone.startswith("98") and len(phone) == 12:
        phone = "0" + phone[2:]

    return phone


def validate_iranian_phone(phone: str) -> str:
    normalized_phone = normalize_phone(phone)

    if not IRANIAN_PHONE_PATTERN.fullmatch(normalized_phone):
        raise ValidationError(
            "شماره موبایل باید ۱۱ رقم و با 09 شروع شود."
        )

    return normalized_phone


def validate_otp_code(code: str) -> str:
    normalized_code = str(code).strip()

    if not OTP_CODE_PATTERN.fullmatch(normalized_code):
        raise ValidationError(
            "کد تأیید باید دقیقاً ۶ رقم باشد."
        )

    return normalized_code
