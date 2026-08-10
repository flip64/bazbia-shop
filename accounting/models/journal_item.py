# accounting/models/journal_item.py

from decimal import Decimal

from django.db import models

from .account import Account
from .journal_entry import JournalEntry


class JournalItem(models.Model):

    journal_entry = models.ForeignKey(
        JournalEntry,
        related_name="items",
        on_delete=models.CASCADE,
        verbose_name="سند",
    )

    account = models.ForeignKey(
        Account,
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

    def __str__(self):
        return f"{self.account} - {self.journal_entry}"
