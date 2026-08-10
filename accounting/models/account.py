from django.core.exceptions import ValidationError
from django.db import models


class Account(models.Model):

    class Type(models.TextChoices):
        ASSET = "asset", "دارایی"
        LIABILITY = "liability", "بدهی"
        EQUITY = "equity", "سرمایه"
        INCOME = "income", "درآمد"
        EXPENSE = "expense", "هزینه"

    code = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="کد حساب",
    )

    name = models.CharField(
        max_length=150,
        verbose_name="نام حساب",
    )

    account_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        verbose_name="نوع حساب",
    )

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.PROTECT,
        verbose_name="حساب والد",
    )

    allow_posting = models.BooleanField(
        default=True,
        verbose_name="امکان ثبت سند",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["code"]
        verbose_name = "حساب"
        verbose_name_plural = "حساب‌ها"

    def clean(self):
        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError(
                {"parent": "یک حساب نمی‌تواند والد خودش باشد."}
            )

    def __str__(self):
        return f"{self.code} - {self.name}"
