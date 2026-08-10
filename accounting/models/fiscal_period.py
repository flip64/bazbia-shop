from django.core.exceptions import ValidationError
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

    def clean(self):
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError(
                    {
                        "end_date":
                            "تاریخ پایان باید بعد از تاریخ شروع باشد."
                    }
                )

            overlapping = FiscalPeriod.objects.filter(
                start_date__lte=self.end_date,
                end_date__gte=self.start_date,
            )

            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)

            if overlapping.exists():
                raise ValidationError(
                    "این دوره مالی با یک دوره مالی دیگر هم‌پوشانی دارد."
                )

    def __str__(self):
        return self.name
