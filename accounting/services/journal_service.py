from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce

from accounting.models import (
    JournalEntry,
    JournalItem,
)


class JournalService:
    """
    سرویس مرکزی مدیریت اسناد حسابداری.
    """

    @staticmethod
    def get_totals(entry: JournalEntry) -> dict:
        """
        مجموع بدهکار و بستانکار یک سند.
        """

        totals = entry.items.aggregate(
            total_debit=Coalesce(
                Sum("debit"),
                Decimal("0"),
            ),
            total_credit=Coalesce(
                Sum("credit"),
                Decimal("0"),
            ),
        )

        return {
            "debit": totals["total_debit"],
            "credit": totals["total_credit"],
        }

    @classmethod
    def validate_balance(cls, entry: JournalEntry):
        """
        بررسی تراز بودن سند.
        """

        totals = cls.get_totals(entry)

        if totals["debit"] <= 0:
            raise ValidationError(
                "سند حسابداری باید حداقل یک مبلغ بدهکار داشته باشد."
            )

        if totals["credit"] <= 0:
            raise ValidationError(
                "سند حسابداری باید حداقل یک مبلغ بستانکار داشته باشد."
            )

        if totals["debit"] != totals["credit"]:
            raise ValidationError(
                (
                    "سند حسابداری تراز نیست. "
                    f"جمع بدهکار: {totals['debit']:,} - "
                    f"جمع بستانکار: {totals['credit']:,}"
                )
            )

        return totals

    @staticmethod
    def validate_items(entry: JournalEntry):
        """
        بررسی ردیف‌های سند.
        """

        items = entry.items.select_related("account")

        if items.count() < 2:
            raise ValidationError(
                "سند حسابداری باید حداقل دو ردیف داشته باشد."
            )

        for item in items:
            item.full_clean()

    @classmethod
    @transaction.atomic
    def post(cls, entry: JournalEntry) -> JournalEntry:
        """
        نهایی کردن سند حسابداری.
        """

        entry = (
            JournalEntry.objects
            .select_for_update()
            .select_related("fiscal_period")
            .get(pk=entry.pk)
        )

        if entry.status == JournalEntry.Status.POSTED:
            return entry

        if entry.status == JournalEntry.Status.CANCELLED:
            raise ValidationError(
                "سند باطل‌شده قابل ثبت نهایی نیست."
            )

        if entry.fiscal_period.is_closed:
            raise ValidationError(
                "دوره مالی این سند بسته شده است."
            )

        entry.full_clean()

        cls.validate_items(entry)
        cls.validate_balance(entry)

        entry.status = JournalEntry.Status.POSTED

        entry.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return entry
