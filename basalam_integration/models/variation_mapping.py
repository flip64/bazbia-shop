from django.core.exceptions import ValidationError
from django.db import models


class BasalamVariationMapping(models.Model):
    """
    اتصال واریانت بازبیا به تنوع محصول باسلام.
    """

    variant = models.OneToOneField(
        "products.ProductVariant",
        on_delete=models.CASCADE,
        related_name="basalam_mapping",
        verbose_name="واریانت بازبیا",
    )

    product_mapping = models.ForeignKey(
        "basalam_integration.BasalamProductMapping",
        on_delete=models.CASCADE,
        related_name="variation_mappings",
        verbose_name="محصول متصل به باسلام",
    )

    basalam_variation_id = models.PositiveBigIntegerField(
        unique=True,
        verbose_name="شناسه تنوع در باسلام",
    )

    last_synced_price = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        null=True,
        blank=True,
        verbose_name="آخرین قیمت همگام‌شده",
    )

    last_synced_stock = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="آخرین موجودی همگام‌شده",
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
        verbose_name = "تنوع متصل به باسلام"
        verbose_name_plural = "تنوع‌های متصل به باسلام"

    def clean(self):
        super().clean()

        if (
            not self.variant_id
            or not self.product_mapping_id
        ):
            return

        if (
            self.variant.product_id
            != self.product_mapping.product_id
        ):
            raise ValidationError(
                {
                    "variant": (
                        "این واریانت متعلق به محصول "
                        "انتخاب‌شده نیست."
                    )
                }
            )

    def __str__(self):
        return (
            f"{self.variant} "
            f"→ {self.basalam_variation_id}"
        )
