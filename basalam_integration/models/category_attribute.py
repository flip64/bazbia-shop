from django.db import models


class BasalamCategoryAttributeSnapshot(models.Model):
    """
    آخرین پاسخ ویژگی‌های یک دسته باسلام.
    """

    basalam_category = models.OneToOneField(
        "basalam_integration.BasalamCategory",
        on_delete=models.CASCADE,
        related_name="attribute_snapshot",
        verbose_name="دسته باسلام",
    )

    raw_payload = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="پاسخ کامل ویژگی‌ها",
    )

    attributes_count = models.PositiveIntegerField(
        default=0,
        verbose_name="تعداد ویژگی‌ها",
    )

    last_error = models.TextField(
        blank=True,
        default="",
        verbose_name="آخرین خطا",
    )

    fetched_at = models.DateTimeField(
        auto_now=True,
        verbose_name="زمان آخرین دریافت",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ایجاد",
    )

    class Meta:
        verbose_name = "ویژگی‌های دسته باسلام"
        verbose_name_plural = "ویژگی‌های دسته‌های باسلام"
        ordering = (
            "basalam_category__title",
        )

    def __str__(self):
        return (
            f"{self.basalam_category.title} "
            f"({self.attributes_count} ویژگی)"
        )
