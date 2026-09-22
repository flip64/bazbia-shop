from decimal import Decimal

from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models


class BasalamCategory(models.Model):
    """
    دسته‌بندی باسلام و درصد کارمزد آن.
    """

    basalam_category_id = models.PositiveBigIntegerField(
        unique=True,
        verbose_name="شناسه دسته در باسلام",
    )

    title = models.CharField(
        max_length=255,
        verbose_name="عنوان دسته در باسلام",
    )

    commission_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("15.00"),
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("99.99")),
        ],
        verbose_name="درصد کارمزد",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ایجاد",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین تغییر",
    )

    class Meta:
        verbose_name = "دسته باسلام"
        verbose_name_plural = "دسته‌ها و کارمزدهای باسلام"
        ordering = ("title",)

    def __str__(self):
        return (
            f"{self.title} "
            f"({self.commission_percent}٪)"
        )
