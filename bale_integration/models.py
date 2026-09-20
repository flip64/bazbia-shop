from django.db import models
from django.utils import timezone


class BaleProductPost(models.Model):
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="bale_posts",
        verbose_name="محصول",
    )
    publication_date = models.DateField(
        default=timezone.localdate,
        unique=True,
        verbose_name="تاریخ انتشار",
    )
    channel_id = models.CharField(max_length=255, verbose_name="کانال")
    message_id = models.BigIntegerField(
        blank=True,
        null=True,
        verbose_name="شناسه پیام",
    )
    is_successful = models.BooleanField(
        default=False,
        verbose_name="ارسال موفق",
    )
    attempt_count = models.PositiveIntegerField(
        default=0,
        verbose_name="تعداد تلاش",
    )
    error_message = models.TextField(blank=True, verbose_name="متن خطا")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین تغییر")

    class Meta:
        ordering = ("-publication_date", "-created_at")
        verbose_name = "انتشار محصول در بله"
        verbose_name_plural = "انتشار محصولات در بله"

    def __str__(self):
        return f"{self.publication_date} - {self.product}"
