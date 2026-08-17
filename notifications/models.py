from django.db import models


class NotificationDelivery(models.Model):
    """وضعیت ارسال هر اعلان برای جلوگیری از ارسال تکراری."""

    class Event(models.TextChoices):
        ORDER_PAID = "order_paid", "پرداخت موفق سفارش"

    class Channel(models.TextChoices):
        SMS = "sms", "پیامک مشتری"
        ADMIN_EMAIL = "admin_email", "ایمیل مدیر"

    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار ارسال"
        SENT = "sent", "ارسال‌شده"
        FAILED = "failed", "ناموفق"

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="notification_deliveries",
        verbose_name="سفارش",
    )
    payment = models.ForeignKey(
        "payments.Payment",
        on_delete=models.CASCADE,
        related_name="notification_deliveries",
        verbose_name="پرداخت",
    )
    event = models.CharField(
        max_length=30,
        choices=Event.choices,
        verbose_name="رویداد",
    )
    channel = models.CharField(
        max_length=30,
        choices=Channel.choices,
        verbose_name="کانال",
    )
    recipient = models.CharField(
        max_length=254,
        blank=True,
        default="",
        verbose_name="گیرنده",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name="وضعیت",
    )
    attempt_count = models.PositiveIntegerField(
        default=0,
        verbose_name="تعداد تلاش",
    )
    provider_response = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="پاسخ سرویس‌دهنده",
    )
    last_error = models.TextField(
        blank=True,
        default="",
        verbose_name="آخرین خطا",
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان ارسال",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ارسال اعلان"
        verbose_name_plural = "ارسال اعلان‌ها"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["payment", "event", "channel"],
                name="unique_payment_event_channel",
            )
        ]

    def __str__(self):
        return (
            f"{self.get_event_display()} - "
            f"{self.get_channel_display()} - "
            f"{self.get_status_display()}"
        )
