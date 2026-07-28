from django.db import models
from orders.models import Order
from django.utils import timezone

# ==============================
# مدل پرداخت (Payment)
# ==============================





class Payment(models.Model):
    """
    تراکنش پرداخت یک سفارش.

    هر بار تلاش برای پرداخت می‌تواند یک رکورد جدید ایجاد کند.
    بنابراین یک سفارش ممکن است چند تراکنش ناموفق و یک
    تراکنش موفق داشته باشد.
    """

    class Status(models.TextChoices):
        PENDING = (
            "pending",
            "در انتظار پرداخت",
        )

        PROCESSING = (
            "processing",
            "در حال پردازش",
        )

        SUCCESSFUL = (
            "successful",
            "موفق",
        )

        FAILED = (
            "failed",
            "ناموفق",
        )

        CANCELLED = (
            "cancelled",
            "لغوشده",
        )

    class Method(models.TextChoices):
        ONLINE = (
            "online",
            "پرداخت آنلاین",
        )

        COD = (
            "cod",
            "پرداخت در محل",
        )

        CARD_TO_CARD = (
            "card_to_card",
            "کارت به کارت",
        )

        WALLET = (
            "wallet",
            "کیف پول",
        )

    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name="سفارش",
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name="مبلغ پرداخت",
        help_text="مبلغ بر حسب تومان",
    )

    payment_method = models.CharField(
        max_length=30,
        choices=Method.choices,
        default=Method.ONLINE,
        verbose_name="روش پرداخت",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name="وضعیت پرداخت",
    )

    gateway = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="درگاه پرداخت",
    )

    authority = models.CharField(
        max_length=100,
        blank=True,
        default="",
        db_index=True,
        verbose_name="شناسه تراکنش درگاه",
    )

    tracking_code = models.CharField(
        max_length=100,
        blank=True,
        default="",
        db_index=True,
        verbose_name="کد رهگیری پرداخت",
    )

    reference_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="شماره مرجع بانکی",
    )

    gateway_response = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="پاسخ درگاه",
    )

    error_message = models.TextField(
        blank=True,
        default="",
        verbose_name="پیام خطا",
    )

    proof_image = models.ImageField(
        upload_to="payment_proofs/",
        blank=True,
        null=True,
        verbose_name="تصویر رسید",
    )

    paid_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="زمان پرداخت موفق",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ایجاد",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی",
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["order", "status"],
            ),
            models.Index(
                fields=["authority"],
            ),
        ]

        verbose_name = "پرداخت"
        verbose_name_plural = "پرداخت‌ها"

    def __str__(self):
        return (
            f"Payment #{self.pk} - "
            f"Order #{self.order_id}"
        )

    @property
    def is_successful(self):
        """
        سازگاری با بخش‌هایی که قبلاً is_successful
        را استفاده می‌کردند.
        """

        return (
            self.status
            == self.Status.SUCCESSFUL
        )

    def mark_successful(
        self,
        tracking_code="",
        reference_id="",
        gateway_response=None,
    ):
        """
        ثبت تراکنش به‌عنوان پرداخت موفق.
        """

        self.status = self.Status.SUCCESSFUL
        self.tracking_code = tracking_code
        self.reference_id = reference_id
        self.paid_at = timezone.now()
        self.error_message = ""

        if gateway_response is not None:
            self.gateway_response = (
                gateway_response
            )

        self.save(
            update_fields=[
                "status",
                "tracking_code",
                "reference_id",
                "paid_at",
                "error_message",
                "gateway_response",
                "updated_at",
            ],
        )

    def mark_failed(
        self,
        error_message="",
        gateway_response=None,
    ):
        """
        ثبت تراکنش به‌عنوان ناموفق.
        """

        self.status = self.Status.FAILED
        self.error_message = error_message

        if gateway_response is not None:
            self.gateway_response = (
                gateway_response
            )

        self.save(
            update_fields=[
                "status",
                "error_message",
                "gateway_response",
                "updated_at",
            ],
        )

# ==============================
# برنامه اقساط سفارش (InstallmentPlan)
# ==============================
class InstallmentPlan(models.Model):
    order = models.OneToOneField(
        'orders.Order', on_delete=models.CASCADE,
        related_name='installment_plan'
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    months = models.PositiveIntegerField(help_text="تعداد ماه‌های پرداخت")
    monthly_amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"اقساط سفارش #{self.order.id}"


# ==============================
# پرداخت هر قسط (InstallmentPayment)
# ==============================
class InstallmentPayment(models.Model):
    plan = models.ForeignKey(
        InstallmentPlan, on_delete=models.CASCADE,
        related_name='payments'
    )
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(blank=True, null=True)

    # جریمه دیرکرد
    late_fee = models.DecimalField(
        max_digits=12, decimal_places=2,
        default=0, help_text='مقدار جریمه دیرکرد (در صورت وجود)'
    )

    def __str__(self):
        return f"قسط {self.due_date} - سفارش #{self.plan.order.id}"
