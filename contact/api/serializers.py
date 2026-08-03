import re

from rest_framework import serializers

from contact.models import ContactMessage


class ContactMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = (
            "id",
            "name",
            "phone",
            "email",
            "subject",
            "order_number",
            "message",
            "created_at",
        )

        read_only_fields = (
            "id",
            "created_at",
        )

    def validate_name(self, value):
        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "نام و نام خانوادگی باید حداقل ۳ کاراکتر باشد."
            )

        return value

    def validate_phone(self, value):
        value = value.strip()

        translation_table = str.maketrans(
            "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
            "01234567890123456789",
        )

        value = value.translate(translation_table)

        value = re.sub(
            r"[\s\-\(\)]",
            "",
            value,
        )

        if value.startswith("+98"):
            value = "0" + value[3:]

        elif value.startswith("0098"):
            value = "0" + value[4:]

        if not re.fullmatch(r"09\d{9}", value):
            raise serializers.ValidationError(
                "شماره موبایل معتبر نیست."
            )

        return value

    def validate_email(self, value):
        return value.strip().lower() if value else ""

    def validate_message(self, value):
        value = value.strip()

        if len(value) < 10:
            raise serializers.ValidationError(
                "متن پیام باید حداقل ۱۰ کاراکتر باشد."
            )

        return value

    def validate_order_number(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "شماره سفارش معتبر نیست."
            )

        return value
