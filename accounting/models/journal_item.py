from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class JournalItem(models.Model):

    journal_entry = models.ForeignKey(
        "accounting.JournalEntry",
        related_name="items",
        on_delete=models.CASCADE,
        verbose_name="سند",
    )

    account = models.ForeignKey(
        "accounting.Account",
        related_name="journal_items",
        on_delete=models.PROTECT,
        verbose_name="حساب",
    )

    debit = models.DecimalField(
        max_digits=18,
        decimal_places=0,
        default=Decimal("0"),
        verbose_name="بدهکار",
    )

    credit = models.DecimalField(
        max_digits=18,
        decimal_places=0,
        default=Decimal("0"),
        verbose_name="بستانکار",
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="شرح ردیف",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "ردیف سند"
        verbose_name_plural = "ردیف‌های سند"

        constraints = [
            models.CheckConstraint(
                condition=Q(debit__gte=0),
                name="journal_item_debit_gte_zero",
            ),

            models.CheckConstraint(
                condition=Q(credit__gte=0),
                name="journal_item_credit_gte_zero",
            ),

            models.CheckConstraint(
                condition=(
                    Q(debit__gt=0, credit=0)
                    | Q(debit=0, credit__gt=0)
                ),
                name="journal_item_debit_or_credit",
            ),
        ]

    def clean(self):
        if self.debit < 0 or self.credit < 0:
            raise ValidationError(
                "مبلغ بدهکار و بستانکار نمی‌تواند منفی باشد."
            )

        if self.debit > 0 and self.credit > 0:
            raise ValidationError(
                "یک ردیف نمی‌تواند همزمان بدهکار و بستانکار باشد."
            )

        if self.debit == 0 and self.credit == 0:
            raise ValidationError(
                "ردیف سند باید مبلغ بدهکار یا بستانکار داشته باشد."
            )

        if self.account_id:
            if not self.account.is_active:
                raise ValidationError(
                    {"account": "حساب انتخاب‌شده غیرفعال است."}
                )

            if not self.account.allow_posting:
                raise ValidationError(
                    {
                        "account":
                            "امکان ثبت سند روی حساب گروهی وجود ندارد."
                    }
                )

    def __str__(self):
        return (
            f"{self.journal_entry} - "
            f"{self.account}"
        )
