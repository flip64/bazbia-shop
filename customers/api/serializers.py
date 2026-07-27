import re

from django.contrib.auth import authenticate
from rest_framework import serializers
from customers.models import (Customer,CustomerAddress)

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
    

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

from rest_framework import serializers

from customers.models import CustomerAddress


class CustomerAddressSerializer(serializers.ModelSerializer):
    """
    Serializer مربوط به آدرس‌های مشتری.

    این Serializer برای عملیات زیر استفاده می‌شود:

    - نمایش آدرس‌های مشتری واردشده
    - ثبت آدرس جدید
    - ویرایش آدرس
    - انتخاب آدرس پیش‌فرض

    فیلد customer از سمت کاربر دریافت نمی‌شود.
    مشتری در View و از طریق request.user تعیین خواهد شد.
    """

    class Meta:
    model = CustomerAddress

    fields = [
        "id",
        "title",
        "recipient_name",
        "recipient_phone",
        "province",
        "city",
        "address",
        "postal_code",
        "is_default",
        "created_at",
        "updated_at",
    ]

    read_only_fields = [
        "id",
        "created_at",
        "updated_at",
    ]

    extra_kwargs = {
        "recipient_name": {
            "required": True,
            "allow_blank": False,
        },
        "recipient_phone": {
            "required": True,
            "allow_blank": False,
        },
        "province": {
            "required": True,
            "allow_blank": False,
        },
        "city": {
            "required": True,
            "allow_blank": False,
        },
        "address": {
            "required": True,
            "allow_blank": False,
        },
        "postal_code": {
            "required": True,
            "allow_blank": False,
        },
    }

    def validate_recipient_name(
        self,
        value: str,
    ) -> str:
        """
        اعتبارسنجی نام تحویل‌گیرنده.
        """

        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "نام تحویل‌گیرنده را کامل وارد کنید."
            )

        return value

    def validate_recipient_phone(
        self,
        value: str,
    ) -> str:
        """
        اعتبارسنجی شماره موبایل تحویل‌گیرنده.

        شماره موبایل باید:

        - فقط شامل عدد باشد
        - با 09 شروع شود
        - دقیقاً 11 رقم داشته باشد
        """

        value = self.normalize_digits(value)

        if not value.isdigit():
            raise serializers.ValidationError(
                "شماره موبایل فقط باید شامل عدد باشد."
            )

        if not value.startswith("09"):
            raise serializers.ValidationError(
                "شماره موبایل باید با 09 شروع شود."
            )

        if len(value) != 11:
            raise serializers.ValidationError(
                "شماره موبایل باید دقیقاً ۱۱ رقم باشد."
            )

        return value

    def validate_postal_code(
        self,
        value: str,
    ) -> str:
        """
        اعتبارسنجی کد پستی.

        کد پستی باید دقیقاً 10 رقم باشد.
        """

        value = self.normalize_digits(value)

        if not value.isdigit():
            raise serializers.ValidationError(
                "کد پستی فقط باید شامل عدد باشد."
            )

        if len(value) != 10:
            raise serializers.ValidationError(
                "کد پستی باید دقیقاً ۱۰ رقم باشد."
            )

        return value

    def validate_province(
        self,
        value: str,
    ) -> str:
        """
        پاک‌سازی و اعتبارسنجی نام استان.
        """

        value = value.strip()

        if len(value) < 2:
            raise serializers.ValidationError(
                "نام استان را وارد کنید."
            )

        return value

    def validate_city(
        self,
        value: str,
    ) -> str:
        """
        پاک‌سازی و اعتبارسنجی نام شهر.
        """

        value = value.strip()

        if len(value) < 2:
            raise serializers.ValidationError(
                "نام شهر را وارد کنید."
            )

        return value

    def validate_address(
        self,
        value: str,
    ) -> str:
        """
        اعتبارسنجی نشانی کامل.
        """

        value = value.strip()

        if len(value) < 10:
            raise serializers.ValidationError(
                "نشانی کامل محل تحویل را وارد کنید."
            )

        return value

    @staticmethod
    def normalize_digits(value: str) -> str:
        """
        تبدیل اعداد فارسی و عربی به اعداد انگلیسی.

        نمونه:

            ۰۹۱۲۳۴۵۶۷۸۹
            ٠٩١٢٣٤٥٦٧٨٩

        به:

            09123456789
        """

        persian_digits = "۰۱۲۳۴۵۶۷۸۹"
        arabic_digits = "٠١٢٣٤٥٦٧٨٩"
        english_digits = "0123456789"

        translation_table = str.maketrans(
            persian_digits + arabic_digits,
            english_digits + english_digits,
        )

        return str(value).translate(
            translation_table
        ).strip()
