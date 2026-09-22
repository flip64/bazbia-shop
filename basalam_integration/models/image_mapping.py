from django.db import models


class BasalamImageMapping(models.Model):
    """
    نگهداری شناسه فایل آپلودشده در باسلام.
    """

    product_image = models.OneToOneField(
        "products.ProductImage",
        on_delete=models.CASCADE,
        related_name="basalam_mapping",
        verbose_name="تصویر محصول بازبیا",
    )

    basalam_file_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="شناسه فایل در باسلام",
    )

    content_hash = models.CharField(
        max_length=64,
        verbose_name="هش محتوای تصویر",
    )

    last_synced_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین همگام‌سازی",
    )

    last_error = models.TextField(
        blank=True,
        default="",
        verbose_name="آخرین خطا",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ایجاد",
    )

    class Meta:
        verbose_name = "تصویر متصل به باسلام"
        verbose_name_plural = "تصاویر متصل به باسلام"

    def __str__(self):
        return (
            f"{self.product_image} "
            f"→ {self.basalam_file_id}"
        )
