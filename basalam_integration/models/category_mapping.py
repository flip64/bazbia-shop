from django.db import models


class BasalamCategoryMapping(models.Model):
    """
    اتصال دسته بازبیا به دسته باسلام.

    هر دسته بازبیا فقط یک مقصد دارد؛ ولی چند دسته
    بازبیا می‌توانند به یک دسته باسلام متصل شوند.
    """

    bazbia_category = models.OneToOneField(
        "products.Category",
        on_delete=models.CASCADE,
        related_name="basalam_mapping",
        verbose_name="دسته بازبیا",
    )

    basalam_category = models.ForeignKey(
        "basalam_integration.BasalamCategory",
        on_delete=models.PROTECT,
        related_name="bazbia_mappings",
        verbose_name="دسته باسلام",
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
        verbose_name = "نگاشت دسته باسلام"
        verbose_name_plural = "نگاشت دسته‌های باسلام"

    def __str__(self):
        return (
            f"{self.bazbia_category} "
            f"← {self.basalam_category.title}"
        )
