from django.db import models


class BasalamOrderMapping(models.Model):
    """
    اتصال سفارش باسلام به سفارش بازبیا.

    یکتا بودن basalam_order_id مانع ثبت دوباره
    یک سفارش می‌شود.
    """

    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="basalam_mapping",
        verbose_name="سفارش بازبیا",
    )

    basalam_order_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="شناسه سفارش باسلام",
    )

    basalam_status = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="آخرین وضعیت باسلام",
    )

    raw_payload = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="آخرین اطلاعات دریافتی",
    )

    last_synced_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین همگام‌سازی",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ثبت",
    )

    class Meta:
        verbose_name = "سفارش باسلام"
        verbose_name_plural = "سفارش‌های باسلام"
        ordering = ("-created_at",)

    def __str__(self):
        return (
            f"سفارش باسلام "
            f"{self.basalam_order_id}"
        )
