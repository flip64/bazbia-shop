from django.db import models


class BasalamProductMapping(models.Model):
    """
    اتصال محصول بازبیا به محصول ساخته‌شده در باسلام.
    """

    product = models.OneToOneField(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="basalam_mapping",
        verbose_name="محصول بازبیا",
    )

    basalam_product_id = models.PositiveBigIntegerField(
        unique=True,
        verbose_name="شناسه محصول در باسلام",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال",
    )

    last_synced_at = models.DateTimeField(
        null=True,
        blank=True,
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

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین تغییر",
    )

    class Meta:
        verbose_name = "محصول متصل به باسلام"
        verbose_name_plural = "محصولات متصل به باسلام"

    def __str__(self):
        return (
            f"{self.product} "
            f"→ {self.basalam_product_id}"
        )
