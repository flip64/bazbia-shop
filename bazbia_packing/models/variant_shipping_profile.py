from decimal import Decimal
from typing import Optional

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class VariantShippingProfile(models.Model):
    """
    مشخصات فیزیکی و قوانین بسته‌بندی هر ProductVariant.

    واحدها:
    - وزن: گرم
    - ابعاد: سانتی‌متر
    - حجم: سانتی‌متر مکعب
    """

    variant = models.OneToOneField(
        "products.ProductVariant",
        on_delete=models.CASCADE,
        related_name="shipping_profile",
        verbose_name="تنوع محصول",
    )

    # =========================================================
    # مشخصات فیزیکی
    # =========================================================

    weight_grams = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(
                1,
                message="وزن محصول باید بیشتر از صفر باشد.",
            )
        ],
        verbose_name="وزن محصول به گرم",
        help_text=(
            "وزن یک واحد محصول همراه با بسته‌بندی کارخانه، "
            "بدون بسته‌بندی حفاظتی بازبیا."
        ),
    )

    length_cm = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="طول به سانتی‌متر",
    )

    width_cm = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="عرض به سانتی‌متر",
    )

    height_cm = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="ارتفاع به سانتی‌متر",
    )

    # =========================================================
    # جهت قرارگیری و قابلیت چرخش
    # =========================================================

    can_rotate = models.BooleanField(
        default=True,
        verbose_name="قابل چرخش",
        help_text=(
            "اگر فعال باشد موتور می‌تواند جهت محصول را "
            "برای پیدا کردن چیدمان مناسب تغییر دهد."
        ),
    )

    must_remain_upright = models.BooleanField(
        default=False,
        verbose_name="باید ایستاده بماند",
        help_text=(
            "محصول نباید روی پهلو یا وارونه قرار بگیرد. "
            "چرخش افقی طول و عرض همچنان می‌تواند مجاز باشد."
        ),
    )

    can_turn_upside_down = models.BooleanField(
        default=True,
        verbose_name="قابل وارونه شدن",
        help_text="آیا محصول می‌تواند به‌صورت وارونه قرار بگیرد؟",
    )

    # =========================================================
    # شکنندگی و قابلیت روی‌هم‌چینی
    # =========================================================

    is_fragile = models.BooleanField(
        default=False,
        verbose_name="شکستنی",
    )

    can_stack_on_others = models.BooleanField(
        default=True,
        verbose_name="قابل قرارگیری روی محصولات دیگر",
        help_text=(
            "آیا این محصول می‌تواند روی محصول دیگری "
            "قرار داده شود؟"
        ),
    )

    can_have_items_on_top = models.BooleanField(
        default=True,
        verbose_name="قابل تحمل محصول روی خود",
        help_text=(
            "آیا می‌توان محصولات دیگر را روی این محصول قرار داد؟"
        ),
    )

    max_top_load_grams = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="حداکثر وزن قابل تحمل روی محصول",
        help_text=(
            "حداکثر وزن مجاز محصولات قرارگرفته روی این کالا "
            "به گرم. خالی یعنی محدودیت عددی ثبت نشده است."
        ),
    )

    # =========================================================
    # نوع و ماهیت محصول
    # =========================================================

    is_liquid = models.BooleanField(
        default=False,
        verbose_name="مایع",
    )

    is_food = models.BooleanField(
        default=False,
        verbose_name="خوراکی",
    )

    is_chemical = models.BooleanField(
        default=False,
        verbose_name="شیمیایی یا شوینده",
    )

    is_hazardous = models.BooleanField(
        default=False,
        verbose_name="دارای محدودیت حمل",
        help_text=(
            "برای کالاهایی که حمل آن‌ها نیازمند قوانین خاص است."
        ),
    )

    # =========================================================
    # بسته‌بندی حفاظتی
    # =========================================================

    requires_bubble_wrap = models.BooleanField(
        default=False,
        verbose_name="نیازمند ضربه‌گیر",
    )

    padding_cm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="حاشیه حفاظتی در هر طرف",
        help_text=(
            "فضای اضافه موردنیاز در هر طرف محصول به سانتی‌متر. "
            "مثلاً مقدار ۱ یعنی دو سانتی‌متر به هر بُعد اضافه می‌شود."
        ),
    )

    extra_packaging_weight_grams = models.PositiveIntegerField(
        default=0,
        verbose_name="وزن بسته‌بندی حفاظتی اضافه",
        help_text=(
            "وزن فوم، نایلون، ضربه‌گیر و بسته‌بندی اضافی "
            "برای هر واحد محصول."
        ),
    )

    # =========================================================
    # جداسازی و ناسازگاری
    # =========================================================

    requires_separate_package = models.BooleanField(
        default=False,
        verbose_name="نیازمند بسته‌بندی جداگانه",
    )

    compatibility_group = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="گروه سازگاری بسته‌بندی",
        help_text=(
            "برای گروه‌بندی کالاها مانند food، chemical، "
            "liquid یا fragile."
        ),
    )

    # =========================================================
    # مدیریت
    # =========================================================

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال",
    )

    notes = models.TextField(
        blank=True,
        default="",
        verbose_name="توضیحات بسته‌بندی",
        help_text="توضیحات ویژه برای انباردار یا موتور بسته‌بندی.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین ویرایش",
    )

    class Meta:
        verbose_name = "مشخصات ارسال تنوع محصول"
        verbose_name_plural = "مشخصات ارسال تنوع‌های محصول"
        ordering = [
            "variant__product__name",
            "variant__sku",
        ]

    def __str__(self) -> str:
        return f"مشخصات ارسال {self.variant}"

    def clean(self) -> None:
        super().clean()

        errors = {}

        dimensions = [
            self.length_cm,
            self.width_cm,
            self.height_cm,
        ]

        entered_dimensions = sum(
            value is not None
            for value in dimensions
        )

        # ابعاد باید یا کاملاً خالی یا کاملاً پر باشند.
        if entered_dimensions not in (0, 3):
            message = (
                "طول، عرض و ارتفاع باید همگی با هم وارد شوند."
            )

            if self.length_cm is None:
                errors["length_cm"] = message

            if self.width_cm is None:
                errors["width_cm"] = message

            if self.height_cm is None:
                errors["height_cm"] = message

        if (
            self.extra_packaging_weight_grams > 0
            and self.weight_grams is None
        ):
            errors["extra_packaging_weight_grams"] = (
                "برای ثبت وزن بسته‌بندی اضافه، "
                "وزن اصلی محصول را نیز وارد کنید."
            )

        if self.must_remain_upright and self.can_turn_upside_down:
            errors["can_turn_upside_down"] = (
                "محصولی که باید ایستاده بماند "
                "نمی‌تواند وارونه شود."
            )

        if (
            not self.can_have_items_on_top
            and self.max_top_load_grams not in (None, 0)
        ):
            errors["max_top_load_grams"] = (
                "وقتی قرار دادن محصول روی این کالا ممنوع است، "
                "حداکثر وزن روی محصول باید خالی یا صفر باشد."
            )

        if self.is_liquid and not self.must_remain_upright:
            errors["must_remain_upright"] = (
                "کالای مایع باید در حالت ایستاده بسته‌بندی شود."
            )

        if self.is_liquid and self.can_turn_upside_down:
            errors["can_turn_upside_down"] = (
                "کالای مایع نباید وارونه قرار بگیرد."
            )

        if self.is_fragile and not self.requires_bubble_wrap:
            errors["requires_bubble_wrap"] = (
                "برای کالای شکستنی، نیاز به ضربه‌گیر را فعال کنید."
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    # =========================================================
    # مشخصات محاسباتی
    # =========================================================

    @property
    def has_complete_dimensions(self) -> bool:
        return all(
            value is not None and value > 0
            for value in [
                self.length_cm,
                self.width_cm,
                self.height_cm,
            ]
        )

    @property
    def has_weight(self) -> bool:
        return (
            self.weight_grams is not None
            and self.weight_grams > 0
        )

    @property
    def is_complete(self) -> bool:
        return (
            self.is_active
            and self.has_weight
            and self.has_complete_dimensions
        )

    @property
    def volume_cm3(self) -> Optional[Decimal]:
        if not self.has_complete_dimensions:
            return None

        return (
            self.length_cm
            * self.width_cm
            * self.height_cm
        )

    @property
    def total_weight_grams(self) -> Optional[int]:
        if not self.has_weight:
            return None

        return (
            self.weight_grams
            + self.extra_packaging_weight_grams
        )

    @property
    def effective_length_cm(self) -> Optional[Decimal]:
        if self.length_cm is None:
            return None

        return self.length_cm + (self.padding_cm * 2)

    @property
    def effective_width_cm(self) -> Optional[Decimal]:
        if self.width_cm is None:
            return None

        return self.width_cm + (self.padding_cm * 2)

    @property
    def effective_height_cm(self) -> Optional[Decimal]:
        if self.height_cm is None:
            return None

        return self.height_cm + (self.padding_cm * 2)

    @property
    def effective_volume_cm3(self) -> Optional[Decimal]:
        if not self.has_complete_dimensions:
            return None

        return (
            self.effective_length_cm
            * self.effective_width_cm
            * self.effective_height_cm
        )

    def calculate_volumetric_weight_grams(
        self,
        divisor: Decimal = Decimal("5000"),
    ) -> Optional[int]:
        if divisor <= 0:
            raise ValueError(
                "ضریب وزن حجمی باید بیشتر از صفر باشد."
            )

        volume = self.effective_volume_cm3

        if volume is None:
            return None

        volumetric_weight_grams = (
            volume / divisor
        ) * Decimal("1000")

        return int(
            volumetric_weight_grams.to_integral_value(
                rounding="ROUND_CEILING",
            )
        )

    def get_chargeable_weight_grams(
        self,
        divisor: Decimal = Decimal("5000"),
    ) -> Optional[int]:
        actual_weight = self.total_weight_grams
        volumetric_weight = (
            self.calculate_volumetric_weight_grams(
                divisor=divisor,
            )
        )

        if actual_weight is None:
            return volumetric_weight

        if volumetric_weight is None:
            return actual_weight

        return max(
            actual_weight,
            volumetric_weight,
        )
