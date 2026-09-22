# basalam_integration/models.py

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models


# =========================================================
# دسته‌بندی‌های باسلام و کارمزد هر دسته
# =========================================================
class BasalamCategory(models.Model):
    """
    اطلاعات دسته‌بندی باسلام و درصد کارمزد آن.

    با تغییر کارمزد باسلام، فقط مقدار commission_percent
    از پنل مدیریت تغییر می‌کند.
    """

    basalam_category_id = models.PositiveBigIntegerField(
        unique=True,
        verbose_name="شناسه دسته در باسلام",
    )

    title = models.CharField(
        max_length=255,
        verbose_name="عنوان دسته در باسلام",
    )

    commission_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("15.00"),
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("99.99")),
        ],
        verbose_name="درصد کارمزد",
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
        verbose_name = "دسته باسلام"
        verbose_name_plural = "دسته‌ها و کارمزدهای باسلام"
        ordering = ("title",)

    def __str__(self):
        return (
            f"{self.title} "
            f"({self.commission_percent}٪)"
        )




# =========================================================
# اتصال دسته بازبیا به دسته باسلام
# =========================================================
class BasalamCategoryAttributeSnapshot(models.Model):
    """
    آخرین پاسخ ویژگی‌های یک دسته باسلام.

    پاسخ کامل API ذخیره می‌شود تا اگر ساختار
    ویژگی‌های باسلام تغییر کرد اطلاعات از بین نرود.
    """

    basalam_category = models.OneToOneField(
        BasalamCategory,
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


# =========================================================
# اتصال محصول بازبیا به محصول باسلام
# =========================================================
class BasalamProductMapping(models.Model):
    """
    شناسه محصول ساخته‌شده در باسلام را برای محصول بازبیا
    نگهداری می‌کند.

    وجود این مدل از ایجاد دوباره محصول در باسلام جلوگیری می‌کند.
    """

    product = models.OneToOneField(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="basalam_mapping",
غییر",
    )

    class Meta:
        verbose_name = "محصول متصل به باسلام"
        verbose_name_plural = "محصولات متصل به باسلام"

    def __str__(self):
        return (
            f"{self.product} "
            f"→ {self.basalam_product_id}"
        )


# =========================================================
# اتصال واریانت بازبیا به تنوع محصول باسلام
# =========================================================
class BasalamVariationMapping(models.Model):
    """
    شناسه تنوع باسلام را برای هر ProductVariant نگهداری می‌کند.

    قیمت و موجودی هر واریانت نیز جداگانه همگام خواهد شد.
    """

    variant = models.OneToOneField(
        "products.ProductVariant",
        on_delete=models.CASCADE,
        related_name="basalam_mapping",
        verbose_name="واریانت بازبیا",
    )

    product_mapping = models.ForeignKey(
        BasalamProductMapping,
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
        """
        واریانت باید متعلق به همان محصولی باشد که
        در product_mapping انتخاب شده است.
        """

        super().clean()

        if not self.variant_id or not self.product_mapping_id:
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


# =========================================================
# اتصال سفارش باسلام به سفارش بازبیا
# =========================================================
class BasalamOrderMapping(models.Model):
    """
    ارتباط میان سفارش باسلام و سفارش ساخته‌شده در بازبیا.

    unique بودن basalam_order_id مانع ثبت دوباره سفارش
    در صورت دریافت چندباره Webhook می‌شود.
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
