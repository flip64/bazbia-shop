# accounting/models/journal_entry.py

from django.db import models


class JournalEntry(models.Model):

    class Type(models.TextChoices):
        SALE = "sale", "فروش"
        PURCHASE = "purchase", "خرید"
        RECEIPT = "receipt", "دریافت"
        PAYMENT = "payment", "پرداخت"
        EXPENSE = "expense", "هزینه"
        REFUND = "refund", "برگشت وجه"
        GATEWAY_SETTLEMENT = (
            "gateway_settlement",
            "تسویه درگاه",
        )
        SUPPLIER_SETTLEMENT = (
            "supplier_settlement",
            "تسویه تأمین‌کننده",
        )
        ADJUSTMENT = "adjustment", "اصلاحی"
        OPENING = "opening", "افتتاحیه"
        CLOSING = "closing", "اختتامیه"

    class Status(models.TextChoices):
        DRAFT = "draft", "پیش‌نویس"
        POSTED = "posted", "ثبت نهایی"
        CANCELLED = "cancelled", "باطل‌شده"

    number = models.PositiveBigIntegerField(
        unique=True,
        verbose_name="شماره سند",
    )

    entry_type = models.CharField(
        max_length=30,
        choices=Type.choices,
        verbose_name="نوع سند",
    )

    date = models.DateField(
        verbose_name="تاریخ سند",
    )

    description = models.TextField(
        blank=True,
        verbose_name="شرح سند",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="وضعیت",
    )

    reference_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="نوع مرجع",
    )

    reference_id = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name="شناسه مرجع",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-date", "-number"]
        verbose_name = "سند حسابداری"
        verbose_name_plural = "اسناد حسابداری"

    def __str__(self):
        return f"سند {self.number}"
