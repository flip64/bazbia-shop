from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce

from accounting.models import (
    JournalEntry,
    JournalItem,
    JournalSequence,
)


class JournalService:
    """
    سرویس مرکزی مدیریت اسناد حسابداری.

    مسئولیت‌ها:
    - ساخت سند
    - ساخت ردیف‌های بدهکار و بستانکار
    - تولید شماره سند
    - بررسی اعتبار ردیف‌ها
    - بررسی تراز بودن سند
    - ثبت نهایی سند
    """

    @staticmethod
    def debit_line(
        *,
        account,
        amount,
        description="",
    ):
        """
        ساخت یک ردیف بدهکار.
        """

        amount = Decimal(str(amount))

        if amount <= 0:
            raise ValidationError(
                "مبلغ ردیف بدهکار باید بزرگ‌تر از صفر باشد."
            )

        return {
            "account": account,
            "debit": amount,
            "credit": Decimal("0"),
            "description": description,
        }

    @staticmethod
    def credit_line(
        *,
        account,
        amount,
        description="",
    ):
        """
        ساخت یک ردیف بستانکار.
        """

        amount = Decimal(str(amount))

        if amount <= 0:
            raise ValidationError(
                "مبلغ ردیف بستانکار باید بزرگ‌تر از صفر باشد."
            )

        return {
            "account": account,
            "debit": Decimal("0"),
            "credit": amount,
            "description": description,
        }

    @staticmethod
    def get_totals(
        entry: JournalEntry,
    ) -> dict:
        """
        محاسبه مجموع بدهکار و بستانکار یک سند.
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
    def validate_balance(
        cls,
        entry: JournalEntry,
    ):
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
    def get_next_number(
        *,
        fiscal_period,
    ) -> int:
        """
        تولید شماره سند بعدی به صورت امن در تراکنش.
        """

        sequence, _ = (
            JournalSequence.objects
            .select_for_update()
            .get_or_create(
                fiscal_period=fiscal_period,
                defaults={
                    "last_number": 0,
                },
            )
        )

        sequence.last_number += 1

        sequence.save(
            update_fields=[
                "last_number",
                "updated_at",
            ]
        )

        return sequence.last_number

    @staticmethod
    def validate_items(
        entry: JournalEntry,
    ):
        """
        بررسی ردیف‌های سند.
        """

        items = list(
            entry.items.select_related("account")
        )

        if len(items) < 2:
            raise ValidationError(
                "سند حسابداری باید حداقل دو ردیف داشته باشد."
            )

        for item in items:
            item.full_clean()

    @classmethod
    @transaction.atomic
    def post(
        cls,
        entry: JournalEntry,
    ) -> JournalEntry:
        """
        ثبت نهایی سند حسابداری.
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

    @classmethod
    @transaction.atomic
    def create_entry(
        cls,
        *,
        fiscal_period,
        entry_type,
        date,
        lines,
        description="",
        reference_type="",
        reference_id=None,
        auto_post=True,
    ) -> JournalEntry:
        """
        ساخت کامل یک سند حسابداری.

        شماره سند به صورت خودکار تولید می‌شود.
        """

        if not lines:
            raise ValidationError(
                "برای سند حسابداری باید ردیف ارسال شود."
            )

        if len(lines) < 2:
            raise ValidationError(
                "سند حسابداری باید حداقل دو ردیف داشته باشد."
            )

        number = cls.get_next_number(
            fiscal_period=fiscal_period,
        )

        entry = JournalEntry(
            number=number,
            fiscal_period=fiscal_period,
            entry_type=entry_type,
            date=date,
            description=description,
            status=JournalEntry.Status.DRAFT,
            reference_type=reference_type,
            reference_id=reference_id,
        )

        entry.full_clean()
        entry.save()

        items = []

        for line in lines:

            if "account" not in line:
                raise ValidationError(
                    "حساب در یکی از ردیف‌های سند مشخص نشده است."
                )

            item = JournalItem(
                journal_entry=entry,
                account=line["account"],
                debit=Decimal(
                    str(
                        line.get(
                            "debit",
                            Decimal("0"),
                        )
                    )
                ),
                credit=Decimal(
                    str(
                        line.get(
                            "credit",
                            Decimal("0"),
                        )
                    )
                ),
                description=line.get(
                    "description",
                    "",
                ),
            )

            item.full_clean()

            items.append(item)

        JournalItem.objects.bulk_create(
            items
        )

        if auto_post:
            entry = cls.post(entry)

        return entry
