from django.db import models
from django.utils import timezone


class TorobVariantConfig(models.Model):
    """
    تنظیمات اتصال هر واریانت محصول به ترب.

    هر ProductVariant می‌تواند به‌صورت مستقل برای ترب
    فعال یا غیرفعال شود.
    """

    variant = models.OneToOneField(
        "products.ProductVariant",
        on_delete=models.CASCADE,
        related_name="torob_config",
        verbose_name="واریانت محصول",
    )

    is_enabled = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="نمایش در ترب",
        help_text="اگر فعال باشد، این واریانت در صورت داشتن موجودی و قیمت معتبر به ترب ارسال می‌شود.",
    )

    page_unique = models.CharField(
        max_length=200,
        unique=True,
        db_index=True,
        editable=False,
        verbose_name="شناسه یکتای ترب",
        help_text="شناسه ثابت واریانت در ترب که نباید در طول زمان تغییر کند.",
    )

    torob_updated_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name="آخرین تغییر مؤثر در ترب",
        help_text="آخرین زمانی که اطلاعات ارسالی این واریانت به ترب تغییر کرده است.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ایجاد",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="زمان ویرایش تنظیمات",
    )

    class Meta:
        verbose_name = "تنظیمات واریانت ترب"
        verbose_name_plural = "تنظیمات واریانت‌های ترب"
        ordering = ["-torob_updated_at"]
        indexes = [
            models.Index(
                fields=["is_enabled", "-torob_updated_at"],
                name="torob_enabled_updated_idx",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.page_unique and self.variant_id:
            self.page_unique = str(self.variant_id)

        super().save(*args, **kwargs)

    @property
    def product_group_id(self):
        """
        شناسه مشترک تمام واریانت‌های یک محصول.
        در دیتابیس ذخیره نمی‌شود چون از محصول والد قابل محاسبه است.
        """
        return str(self.variant.product_id)

    def touch(self, save=True):
        """
        ثبت تغییر مؤثر در اطلاعات خروجی ترب.
        """
        self.torob_updated_at = timezone.now()

        if save:
            self.save(
                update_fields=[
                    "torob_updated_at",
                    "updated_at",
                ]
            )

    def __str__(self):
        status = "فعال" if self.is_enabled else "غیرفعال"

        return (
            f"{self.variant} | "
            f"Torob ID: {self.page_unique} | "
            f"{status}"
        )


class TorobRequestLog(models.Model):
    """
    ثبت درخواست‌های ارسالی ترب برای گزارش‌گیری و تحلیل.
    """

    class RequestType(models.TextChoices):
        PAGINATION = (
            "pagination",
            "دریافت صفحه محصولات",
        )
        PAGE_UNIQUES = (
            "page_uniques",
            "دریافت با شناسه یکتا",
        )
        PAGE_URLS = (
            "page_urls",
            "دریافت با لینک محصول",
        )
        INVALID = (
            "invalid",
            "درخواست نامعتبر",
        )

    class AuthStatus(models.TextChoices):
        VALID = (
            "valid",
            "توکن معتبر",
        )
        INVALID = (
            "invalid",
            "توکن نامعتبر",
        )
        MISSING = (
            "missing",
            "توکن ارسال نشده",
        )
        NOT_CHECKED = (
            "not_checked",
            "بررسی نشده",
        )

    request_type = models.CharField(
        max_length=20,
        choices=RequestType.choices,
        default=RequestType.INVALID,
        db_index=True,
        verbose_name="نوع درخواست",
    )

    method = models.CharField(
        max_length=10,
        default="POST",
        verbose_name="متد درخواست",
    )

    endpoint = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="مسیر endpoint",
    )

    request_body = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="بدنه درخواست",
    )

    page = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="شماره صفحه",
    )

    sort = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="نوع مرتب‌سازی",
    )

    requested_items_count = models.PositiveIntegerField(
        default=0,
        verbose_name="تعداد آیتم‌های درخواستی",
        help_text="تعداد page_unique یا page_url ارسال‌شده توسط ترب.",
    )

    response_status = models.PositiveSmallIntegerField(
        default=200,
        db_index=True,
        verbose_name="کد وضعیت پاسخ",
    )

    products_count = models.PositiveIntegerField(
        default=0,
        verbose_name="تعداد محصولات پاسخ",
    )

    total_products = models.PositiveIntegerField(
        default=0,
        verbose_name="تعداد کل محصولات",
    )

    max_pages = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="تعداد کل صفحات",
    )

    auth_status = models.CharField(
        max_length=20,
        choices=AuthStatus.choices,
        default=AuthStatus.NOT_CHECKED,
        db_index=True,
        verbose_name="وضعیت اعتبارسنجی توکن",
    )

    token_version = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="نسخه توکن ترب",
    )

    error_message = models.TextField(
        blank=True,
        verbose_name="پیام خطا",
    )

    duration_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="مدت پاسخ‌گویی به میلی‌ثانیه",
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="آدرس IP",
    )

    user_agent = models.TextField(
        blank=True,
        verbose_name="User-Agent",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="زمان درخواست",
    )

    class Meta:
        verbose_name = "لاگ درخواست ترب"
        verbose_name_plural = "لاگ درخواست‌های ترب"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["-created_at", "response_status"],
                name="torob_log_date_status_idx",
            ),
            models.Index(
                fields=["request_type", "-created_at"],
                name="torob_log_type_date_idx",
            ),
            models.Index(
                fields=["auth_status", "-created_at"],
                name="torob_log_auth_date_idx",
            ),
        ]

    @property
    def is_successful(self):
        return 200 <= self.response_status < 300

    def __str__(self):
        return (
            f"{self.get_request_type_display()} | "
            f"{self.response_status} | "
            f"{self.created_at}"
        )
