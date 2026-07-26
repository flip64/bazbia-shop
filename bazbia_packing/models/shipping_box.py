# bazbia_packing/models/shipping_box.py

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class ShippingBox(models.Model):
    class PackageType(models.TextChoices):
        POSTAL_BOX = "postal_box", "جعبه پستی"
        CARTON = "carton", "کارتن"
        ENVELOPE = "envelope", "پاکت"
        BUBBLE_ENVELOPE = "bubble_envelope", "پاکت حباب‌دار"
        BAG = "bag", "کیسه یا نایلون"

    name = models.CharField(
        max_length=100,
        verbose_name="نام بسته",
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="کد بسته",
    )

    package_type = models.CharField(
        max_length=30,
        choices=PackageType.choices,
        default=PackageType.POSTAL_BOX,
        verbose_name="نوع بسته",
    )

    # ابعاد داخلی قابل استفاده
    inner_length_cm = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="طول داخلی",
    )

    inner_width_cm = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="عرض داخلی",
    )

    inner_height_cm = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="ارتفاع داخلی",
    )

    # ابعاد خارجی برای محاسبه حمل
    outer_length_cm = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="طول خارجی",
    )

    outer_width_cm = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="عرض خارجی",
    )

    outer_height_cm = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="ارتفاع خارجی",
    )

    empty_weight_grams = models.PositiveIntegerField(
        default=0,
        verbose_name="وزن خالی بسته",
    )

    max_content_weight_grams = models.PositiveIntegerField(
        verbose_name="حداکثر وزن محتویات",
    )

    price = models.PositiveBigIntegerField(
        default=0,
        verbose_name="قیمت بسته به ریال",
    )

    stock = models.PositiveIntegerField(
        default=0,
        verbose_name="موجودی",
    )

    allows_fragile_items = models.BooleanField(
        default=True,
        verbose_name="مناسب کالای شکستنی",
    )

    allows_liquid_items = models.BooleanField(
        default=True,
        verbose_name="مناسب کالای مایع",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "بسته استاندارد"
        verbose_name_plural = "بسته‌های استاندارد"
        ordering = [
            "inner_length_cm",
            "inner_width_cm",
            "inner_height_cm",
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def clean(self):
        super().clean()

        errors = {}

        outer_dimensions = [
            self.outer_length_cm,
            self.outer_width_cm,
            self.outer_height_cm,
        ]

        entered_outer_dimensions = sum(
            value is not None
            for value in outer_dimensions
        )

        if entered_outer_dimensions not in (0, 3):
            message = (
                "ابعاد خارجی باید همگی با هم وارد شوند."
            )

            if self.outer_length_cm is None:
                errors["outer_length_cm"] = message

            if self.outer_width_cm is None:
                errors["outer_width_cm"] = message

            if self.outer_height_cm is None:
                errors["outer_height_cm"] = message

        if (
            self.outer_length_cm is not None
            and self.outer_length_cm < self.inner_length_cm
        ):
            errors["outer_length_cm"] = (
                "طول خارجی نمی‌تواند از طول داخلی کمتر باشد."
            )

        if (
            self.outer_width_cm is not None
            and self.outer_width_cm < self.inner_width_cm
        ):
            errors["outer_width_cm"] = (
                "عرض خارجی نمی‌تواند از عرض داخلی کمتر باشد."
            )

        if (
            self.outer_height_cm is not None
            and self.outer_height_cm < self.inner_height_cm
        ):
            errors["outer_height_cm"] = (
                "ارتفاع خارجی نمی‌تواند از ارتفاع داخلی کمتر باشد."
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def inner_volume_cm3(self):
        return (
            self.inner_length_cm
            * self.inner_width_cm
            * self.inner_height_cm
        )

    @property
    def outer_volume_cm3(self):
        if not all([
            self.outer_length_cm,
            self.outer_width_cm,
            self.outer_height_cm,
        ]):
            return None

        return (
            self.outer_length_cm
            * self.outer_width_cm
            * self.outer_height_cm
        )

    @property
    def total_max_weight_grams(self):
        return (
            self.max_content_weight_grams
            + self.empty_weight_grams
        )
