from django.db import models
from django.utils import timezone


class RubikaProductPost(models.Model):
    TRIGGER_CRON = "cron"
    TRIGGER_MANUAL = "manual"
    TRIGGER_CHOICES = (
        (TRIGGER_CRON, "ارسال تصادفی کرون"),
        (TRIGGER_MANUAL, "ارسال دستی"),
    )

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="rubika_posts",
        verbose_name="محصول",
    )
    publication_date = models.DateField(
        default=timezone.localdate,
        verbose_name="تاریخ انتشار",
    )
    cron_date = models.DateField(
        blank=True,
        null=True,
        unique=True,
        verbose_name="تاریخ اجرای کرون",
    )
    trigger = models.CharField(
        max_length=10,
        choices=TRIGGER_CHOICES,
        default=TRIGGER_CRON,
        verbose_name="روش ارسال",
    )
    channel_id = models.CharField(max_length=255, verbose_name="کانال")
    message_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="شناسه پیام",
    )
    is_successful = models.BooleanField(default=False, verbose_name="ارسال موفق")
    attempt_count = models.PositiveIntegerField(default=0, verbose_name="تعداد تلاش")
    error_message = models.TextField(blank=True, verbose_name="متن خطا")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین تغییر")

    class Meta:
        ordering = ("-publication_date", "-created_at")
        verbose_name = "انتشار محصول در روبیکا"
        verbose_name_plural = "انتشار محصولات در روبیکا"

    def __str__(self):
        return f"{self.publication_date} - {self.product}"
