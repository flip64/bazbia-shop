from django.db import models


class JournalSequence(models.Model):
    """
    نگهداری شماره آخرین سند حسابداری برای هر دوره مالی.
    """

    fiscal_period = models.OneToOneField(
        "accounting.FiscalPeriod",
        related_name="journal_sequence",
        on_delete=models.PROTECT,
        verbose_name="دوره مالی",
    )

    last_number = models.PositiveBigIntegerField(
        default=0,
        verbose_name="آخرین شماره سند",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "شمارنده سند"
        verbose_name_plural = "شمارنده‌های اسناد"

    def __str__(self):
        return (
            f"{self.fiscal_period} - "
            f"آخرین شماره: {self.last_number}"
        )
