"""
مدل مشخصات فیزیکی و بسته‌بندی تنوع محصول.

این فایل اطلاعات موردنیاز برای عملیات زیر را نگهداری می‌کند:

- محاسبه وزن واقعی سفارش
- محاسبه وزن حجمی مرسوله
- انتخاب کارتن مناسب
- تشخیص کالاهای شکستنی
- تشخیص کالاهای نیازمند بسته‌بندی جداگانه
- آماده‌سازی اطلاعات برای سرویس‌های پستی
- استفاده در موتور بسته‌بندی بازبیا

مشخصات فیزیکی به ProductVariant متصل شده‌اند، زیرا ممکن است
تنوع‌های مختلف یک محصول وزن و ابعاد متفاوتی داشته باشند.

مثال:

    شامپو ۵۰۰ میلی‌لیتری
    شامپو ۱۰۰۰ میلی‌لیتری

این دو تنوع متعلق به یک محصول هستند، اما وزن و ابعاد بسته‌بندی
آن‌ها یکسان نیست.
"""

from decimal import Decimal
from typing import Optional

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class VariantShippingProfile(models.Model):
    """
    مشخصات فیزیکی و ارسال یک تنوع محصول.

    هر ProductVariant حداکثر یک پروفایل ارسال دارد. این رابطه
    به‌صورت OneToOne تعریف شده است.

    واحدهای استاندارد این مدل:

    - وزن: گرم
    - طول: سانتی‌متر
    - عرض: سانتی‌متر
    - ارتفاع: سانتی‌متر
    - حجم: سانتی‌متر مکعب

    ابعاد باید مربوط به محصول در حالت آماده قرارگیری در بسته
    ارسال باشند، نه صرفاً ابعاد ظاهری محصول بدون بسته‌بندی.

    برای مثال، اگر یک محصول داخل جعبه کارخانه قرار دارد، ابعاد
    همان جعبه کارخانه ثبت می‌شود. وزن و فضای بسته‌بندی حفاظتی
    اضافه نیز می‌تواند جداگانه ثبت شود.
    """

    variant = models.OneToOneField(
        "products.ProductVariant",
        on_delete=models.CASCADE,
        related_name="shipping_profile",
        verbose_name="تنوع محصول",
        help_text=(
            "تنوع محصولی که این مشخصات فیزیکی و ارسال "
            "به آن تعلق دارد."
        ),
    )

    weight_grams = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(
                1,
                message="وزن محصول باید بیشتر از صفر باشد.",
            ),
        ],
        verbose_name="وزن محصول به گرم",
        help_text=(
            "وزن یک واحد از این تنوع محصول به گرم. "
            "این مقدار شامل بسته‌بندی اصلی محصول است، "
            "اما بسته‌بندی حفاظتی اضافه را شامل نمی‌شود."
        ),
    )

    length_cm = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(
                Decimal("0.01"),
                message="طول محصول باید بیشتر از صفر باشد.",
            ),
        ],
        verbose_name="طول بسته به سانتی‌متر",
        help_text=(
            "طول یک واحد محصول در حالت آماده بسته‌بندی "
            "و بر حسب سانتی‌متر."
        ),
    )

    width_cm = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(
                Decimal("0.01"),
                message="عرض محصول باید بیشتر از صفر باشد.",
            ),
        ],
        verbose_name="عرض بسته به سانتی‌متر",
        help_text=(
            "عرض یک واحد محصول در حالت آماده بسته‌بندی "
            "و بر حسب سانتی‌متر."
        ),
    )

    height_cm = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(
                Decimal("0.01"),
                message="ارتفاع محصول باید بیشتر از صفر باشد.",
            ),
        ],
        verbose_name="ارتفاع بسته به سانتی‌متر",
        help_text=(
            "ارتفاع یک واحد محصول در حالت آماده بسته‌بندی "
            "و بر حسب سانتی‌متر."
        ),
    )

    extra_packaging_weight_grams = models.PositiveIntegerField(
        default=0,
        verbose_name="وزن بسته‌بندی حفاظتی اضافه",
        help_text=(
            "وزن تقریبی ضربه‌گیر، نایلون، فوم یا سایر مواد "
            "بسته‌بندی اضافه برای هر واحد محصول، به گرم."
        ),
    )

    is_fragile = models.BooleanField(
        default=False,
        verbose_name="کالای شکستنی",
        help_text=(
            "اگر محصول شکستنی است و به مراقبت یا ضربه‌گیر "
            "بیشتری نیاز دارد، این گزینه فعال شود."
        ),
    )

    requires_separate_package = models.BooleanField(
        default=False,
        verbose_name="نیازمند بسته‌بندی جداگانه",
        help_text=(
            "اگر محصول نباید همراه سایر محصولات در یک کارتن "
            "قرار بگیرد، این گزینه فعال شود."
        ),
    )

    can_rotate = models.BooleanField(
        default=True,
        verbose_name="قابل چرخش در بسته",
        help_text=(
            "آیا محصول هنگام چیدمان داخل کارتن می‌تواند "
            "در جهت‌های مختلف چرخانده شود؟ برای محصولاتی "
            "مانند مایعات یا کالاهای دارای جهت نگهداری خاص، "
            "این گزینه غیرفعال شود."
        ),
    )

    is_liquid = models.BooleanField(
        default=False,
        verbose_name="کالای مایع",
        help_text=(
            "اگر محصول حاوی مایع است، این گزینه فعال شود. "
            "این اطلاعات می‌تواند برای محدودیت چرخش و "
            "بسته‌بندی ضدنشت استفاده شود."
        ),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال",
        help_text=(
            "اگر غیرفعال باشد، موتور بسته‌بندی نباید از "
            "این پروفایل برای محاسبات جدید استفاده کند."
        ),
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
        """
        نمایش خوانای مدل در پنل مدیریت و Shell.

        نمونه خروجی:

            مشخصات ارسال شامپو یک لیتری - SKU-1001
        """

        return f"مشخصات ارسال {self.variant}"

    def clean(self) -> None:
        """
        اعتبارسنجی منطقی اطلاعات مدل.

        Django به‌صورت پیش‌فرض validatorهای هر فیلد را اجرا
        می‌کند، اما این متد برای اعتبارسنجی‌هایی است که به
        ارتباط چند فیلد با یکدیگر وابسته‌اند.

        قوانین فعلی:

        1. اگر یکی از ابعاد وارد شود، هر سه بعد باید وارد شوند.
        2. کالای مایع به‌صورت پیش‌فرض نباید قابل چرخش باشد.
        3. وزن بسته‌بندی اضافه بدون وزن اصلی قابل استفاده نیست.
        """

        super().clean()

        errors: dict[str, str] = {}

        dimensions = [
            self.length_cm,
            self.width_cm,
            self.height_cm,
        ]

        entered_dimensions_count = sum(
            dimension is not None
            for dimension in dimensions
        )

        if entered_dimensions_count not in (0, 3):
            message = (
                "برای ثبت ابعاد، طول، عرض و ارتفاع باید "
                "همگی وارد شوند."
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
                "برای ثبت وزن بسته‌بندی اضافه، ابتدا وزن "
                "اصلی محصول را وارد کنید."
            )

        if self.is_liquid and self.can_rotate:
            errors["can_rotate"] = (
                "برای کالای مایع بهتر است امکان چرخاندن "
                "در بسته غیرفعال باشد."
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs) -> None:
        """
        ذخیره مدل پس از اجرای اعتبارسنجی کامل.

        اجرای full_clean باعث می‌شود اعتبارسنجی‌های فیلدها
        و متد clean حتی خارج از Django Admin نیز اجرا شوند.
        """

        self.full_clean()

        super().save(*args, **kwargs)

    @property
    def has_complete_dimensions(self) -> bool:
        """
        بررسی کامل بودن طول، عرض و ارتفاع.

        Returns:
            bool:
                اگر هر سه بعد مقدار معتبر داشته باشند True
                و در غیر این صورت False برمی‌گرداند.
        """

        return all(
            dimension is not None and dimension > 0
            for dimension in [
                self.length_cm,
                self.width_cm,
                self.height_cm,
            ]
        )

    @property
    def has_weight(self) -> bool:
        """
        بررسی ثبت بودن وزن اصلی محصول.
        """

        return (
            self.weight_grams is not None
            and self.weight_grams > 0
        )

    @property
    def is_complete(self) -> bool:
        """
        بررسی کامل بودن اطلاعات ضروری ارسال.

        یک پروفایل زمانی کامل محسوب می‌شود که:

        - فعال باشد
        - وزن محصول ثبت شده باشد
        - طول، عرض و ارتفاع ثبت شده باشند
        """

        return (
            self.is_active
            and self.has_weight
            and self.has_complete_dimensions
        )

    @property
    def volume_cm3(self) -> Optional[Decimal]:
        """
        محاسبه حجم یک واحد محصول به سانتی‌متر مکعب.

        فرمول:

            حجم = طول × عرض × ارتفاع

        Returns:
            Decimal | None:
                اگر ابعاد کامل باشند حجم برگردانده می‌شود؛
                در غیر این صورت None برمی‌گردد.
        """

        if not self.has_complete_dimensions:
            return None

        return (
            self.length_cm
            * self.width_cm
            * self.height_cm
        )

    @property
    def total_weight_grams(self) -> Optional[int]:
        """
        محاسبه وزن نهایی یک واحد برای بسته‌بندی.

        وزن نهایی برابر است با:

            وزن محصول + وزن بسته‌بندی حفاظتی اضافه

        Returns:
            int | None:
                اگر وزن اصلی ثبت شده باشد وزن نهایی به گرم
                برگردانده می‌شود؛ در غیر این صورت None.
        """

        if not self.has_weight:
            return None

        return (
            self.weight_grams
            + self.extra_packaging_weight_grams
        )

    def calculate_volumetric_weight_grams(
        self,
        divisor: Decimal = Decimal("5000"),
    ) -> Optional[int]:
        """
        محاسبه وزن حجمی یک واحد محصول.

        بسیاری از شرکت‌های حمل‌ونقل برای کالاهای سبک اما حجیم
        از وزن حجمی استفاده می‌کنند.

        فرمول رایج با ابعاد سانتی‌متر:

            وزن حجمی کیلوگرم =
                طول × عرض × ارتفاع ÷ ضریب حجمی

        ضریب حجمی بسته به شرکت حمل‌ونقل ممکن است متفاوت باشد؛
        برای مثال 5000 یا 6000.

        Args:
            divisor:
                ضریب محاسبه وزن حجمی. مقدار پیش‌فرض 5000 است.

        Returns:
            int | None:
                وزن حجمی به گرم یا None در صورت ناقص بودن
                ابعاد.

        Raises:
            ValueError:
                اگر ضریب صفر یا منفی باشد.
        """

        if divisor <= 0:
            raise ValueError(
                "ضریب وزن حجمی باید بیشتر از صفر باشد."
            )

        volume = self.volume_cm3

        if volume is None:
            return None

        volumetric_weight_kg = volume / divisor

        volumetric_weight_grams = (
            volumetric_weight_kg * Decimal("1000")
        )

        return int(
            volumetric_weight_grams.to_integral_value(
                rounding="ROUND_CEILING",
            )
        )

    def get_chargeable_weight_grams(
        self,
        divisor: Decimal = Decimal("5000"),
    ) -> Optional[int]:
        """
        محاسبه وزن قابل محاسبه برای شرکت حمل‌ونقل.

        شرکت حمل‌ونقل معمولاً بیشترین مقدار میان وزن واقعی
        و وزن حجمی را برای تعیین هزینه استفاده می‌کند.

        Args:
            divisor:
                ضریب محاسبه وزن حجمی.

        Returns:
            int | None:
                بیشترین مقدار وزن واقعی و حجمی به گرم.
        """

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