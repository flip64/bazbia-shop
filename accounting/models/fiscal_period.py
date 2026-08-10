# accounting/models/fiscal_period.py

from django.db import models


class FiscalPeriod(models.Model):

    name = models.CharField(
        max_length=100,
        verbose_name="نام دوره مالی",
    )

    start_date = models.DateField(
        verbose_name="تاریخ شروع",
    )

    end_date = models.DateField(
        verbose_name="تاریخ پایان",
    )

    is_closed = models.BooleanField(
        default=False,
        verbose_name="بسته شده",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-start_date"]
        verbose_name = "دوره مالی"
        verbose_name_plural = "دوره‌های مالی"

    def __str__(self):
        return self.name
