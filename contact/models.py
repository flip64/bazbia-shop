from django.conf import settings
from django.db import models


class ContactMessage(models.Model):
    SUBJECT_ORDER = "order"
    SUBJECT_PAYMENT = "payment"
    SUBJECT_PRODUCT = "product"
    SUBJECT_RETURN = "return"
    SUBJECT_COOPERATION = "cooperation"
    SUBJECT_SUGGESTION = "suggestion"
    SUBJECT_OTHER = "other"

    SUBJECT_CHOICES = [
        (SUBJECT_ORDER, "پیگیری سفارش"),
        (SUBJECT_PAYMENT, "مشکل پرداخت"),
        (SUBJECT_PRODUCT, "سؤال درباره محصول"),
        (SUBJECT_RETURN, "مرجوعی و بازگشت کالا"),
        (SUBJECT_COOPERATION, "همکاری با بازبیا"),
        (SUBJECT_SUGGESTION, "پیشنهاد یا انتقاد"),
        (SUBJECT_OTHER, "سایر موارد"),
    ]

    STATUS_NEW = "new"
    STATUS_REVIEWING = "reviewing"
    STATUS_ANSWERED = "answered"
    STATUS_CLOSED = "closed"

    STATUS_CHOICES = [
        (STATUS_NEW, "جدید"),
        (STATUS_REVIEWING, "در حال بررسی"),
        (STATUS_ANSWERED, "پاسخ داده شده"),
        (STATUS_CLOSED, "بسته شده"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="contact_messages",
        null=True,
        blank=True,
        verbose_name="کاربر",
    )

    name = models.CharField(
        max_length=150,
        verbose_name="نام و نام خانوادگی",
    )

    phone = models.CharField(
        max_length=20,
        db_index=True,
        verbose_name="شماره تماس",
    )

    email = models.EmailField(
        max_length=254,
        blank=True,
        verbose_name="ایمیل",
    )

    subject = models.CharField(
        max_length=30,
        choices=SUBJECT_CHOICES,
        db_index=True,
        verbose_name="موضوع",
    )

    order_number = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="شماره سفارش",
    )

    message = models.TextField(
        max_length=1000,
        verbose_name="متن پیام",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        db_index=True,
        verbose_name="وضعیت",
    )

    admin_note = models.TextField(
        blank=True,
        verbose_name="یادداشت مدیر",
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="آدرس IP",
    )

    user_agent = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="مرورگر کاربر",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="زمان ثبت",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین تغییر",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "پیام تماس"
        verbose_name_plural = "پیام‌های تماس"
        indexes = [
            models.Index(
                fields=["status", "-created_at"],
                name="contact_status_created_idx",
            ),
        ]

    def __str__(self):
        return f"{self.name} - {self.get_subject_display()}"
