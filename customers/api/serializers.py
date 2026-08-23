import re

from django.contrib.auth import authenticate
from rest_framework import serializers


IRAN_PHONE_PATTERN = re.compile(r"^09\d{9}$")


def validate_phone_number(phone: str) -> str:
    """
    اعتبارسنجی و یکسان‌سازی شماره موبایل ایران.
    """

    phone = phone.strip()
    phone = phone.replace(" ", "").replace("-", "")

    if phone.startswith("+98"):
        phone = f"0{phone[3:]}"

    elif phone.startswith("98"):
        phone = f"0{phone[2:]}"

    if not IRAN_PHONE_PATTERN.fullmatch(phone):
        raise serializers.ValidationError(
            "شماره موبایل باید با 09 شروع شود و 11 رقم داشته باشد."
        )

    return phone


class RequestOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(
        max_length=15,
        trim_whitespace=True,
    )

    def validate_phone(self, value):
        return validate_phone_number(value)


class VerifyOTPSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()

    code = serializers.CharField(
        min_length=6,
        max_length=6,
        trim_whitespace=True,
    )

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(
                "کد تأیید باید فقط شامل عدد باشد."
            )

        return value


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(
        max_length=15,
        trim_whitespace=True,
    )

    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    def validate_phone(self, value):
        return validate_phone_number(value)

    def validate(self, attrs):
        phone = attrs.get("phone")
        password = attrs.get("password")

        user = authenticate(
            username=phone,
            password=password,
        )

        if user is None:
            raise serializers.ValidationError(
                {
                    "detail": "شماره موبایل یا رمز عبور اشتباه است."
                }
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {
                    "detail": "حساب کاربری شما غیرفعال است."
                }
            )

        attrs["user"] = user

        return attrs