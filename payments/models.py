# payments/models.py

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from orders.models import Order


# =========================================================
# مدل پرداخت
# =========================================================
class Payment(models.Model):
    """
    تراکنش پرداخت مربوط به یک سفارش.

    هر سفارش می‌تواند چند تلاش پرداخت داشته باشد؛ برای مثال:
    - یک پرداخت ناموفق
    - یک پرداخت لغوشده
    - یک پرداخت موفق

    مبلغ‌ها در کل پروژه بازبیا بر حسب تومان ذخیره می‌شوند.
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

        INSTALLMENT = (
            "installment",
            "پرداخت اقساطی",
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
        validators=[
            MinValueValidator(
                Decimal("0.01"),
            ),
        ],
        verbose_name="مبلغ پرداخت",
        help_text="مبلغ پرداخت بر حسب تومان",
    )

    payment_method = models.CharField(
        max_length=30,
        choices=Method.choices,
        default=Method.ONLINE,
        db_index=True,
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
        help_text="مثلاً zarinpal یا idpay",
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
        db_index=True,
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
        upload_to="payment_proofs/%Y/%m/",
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
        ordering = [
            "-created_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "order",
                    "status",
                ],
                name="payment_order_status_idx",
            ),
            models.Index(
                fields=[
                    "authority",
                ],
                name="payment_authority_idx",
            ),
            models.Index(
                fields=[
                    "tracking_code",
                ],
                name="payment_tracking_idx",
            ),
        ]

        verbose_name = "پرداخت"
        verbose_name_plural = "پرداخت‌ها"

    def __str__(self):
        return (
            f"پرداخت #{self.pk} "
            f"- سفارش #{self.order_id}"
        )

    @property
    def is_successful(self):
        """
        مشخص می‌کند که تراکنش با موفقیت تأیید شده است یا نه.
        """

        return (
            self.status
            == self.Status.SUCCESSFUL
        )

    @property
    def is_final(self):
        """
        مشخص می‌کند که وضعیت پرداخت نهایی شده است یا نه.
        """

        return self.status in {
            self.Status.SUCCESSFUL,
            self.Status.FAILED,
            self.Status.CANCELLED,
        }

    def mark_processing(
        self,
        gateway_response=None,
    ):
        """
        تغییر وضعیت تراکنش به در حال پردازش.
        """

        self.status = self.Status.PROCESSING

        update_fields = [
            "status",
            "updated_at",
        ]

        if gateway_response is not None:
            self.gateway_response = (
                gateway_response
            )

            update_fields.append(
                "gateway_response",
            )

        self.save(
            update_fields=update_fields,
        )

    def mark_successful(
        self,
        tracking_code="",
        reference_id="",
        gateway_response=None,
    ):
        """
        ثبت تراکنش به‌عنوان پرداخت موفق.

        بعد از تأیید موفق درگاه، وضعیت سفارش نیز paid می‌شود.
        """

        self.status = self.Status.SUCCESSFUL
        self.tracking_code = (
            str(tracking_code).strip()
        )
        self.reference_id = (
            str(reference_id).strip()
        )
        self.paid_at = timezone.now()
        self.error_message = ""

        update_fields = [
            "status",
            "tracking_code",
            "reference_id",
            "paid_at",
            "error_message",
            "updated_at",
        ]

        if gateway_response is not None:
            self.gateway_response = (
                gateway_response
            )

            update_fields.append(
                "gateway_response",
            )

        self.save(
            update_fields=update_fields,
        )

        if self.order.status != "paid":
            self.order.status = "paid"

            self.order.save(
                update_fields=[
                    "status",
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
        self.error_message = str(
            error_message
        ).strip()

        update_fields = [
            "status",
            "error_message",
            "updated_at",
        ]

        if gateway_response is not None:
            self.gateway_response = (
                gateway_response
            )

            update_fields.append(
                "gateway_response",
            )

        self.save(
            update_fields=update_fields,
        )

    def mark_cancelled(
        self,
        error_message="",
        gateway_response=None,
    ):
        """
        ثبت تراکنش به‌عنوان لغوشده توسط کاربر یا درگاه.
        """

        self.status = self.Status.CANCELLED
        self.error_message = str(
            error_message
        ).strip()

        update_fields = [
            "status",
            "error_message",
            "updated_at",
        ]

        if gateway_response is not None:
            self.gateway_response = (
                gateway_response
            )

            update_fields.append(
                "gateway_response",
            )

        self.save(
            update_fields=update_fields,
        )


# =========================================================
# برنامه اقساط سفارش
# =========================================================
class InstallmentPlan(models.Model):
    """
    برنامه پرداخت اقساطی یک سفارش.

    هر سفارش حداکثر یک برنامه اقساطی دارد.
    """

    class Status(models.TextChoices):
        DRAFT = (
            "draft",
            "پیش‌نویس",
        )

        ACTIVE = (
            "active",
            "فعال",
        )

        COMPLETED = (
            "completed",
            "تسویه‌شده",
        )

        CANCELLED = (
            "cancelled",
            "لغوشده",
        )

        DEFAULTED = (
            "defaulted",
            "دارای بدهی معوق",
        )

    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        related_name="installment_plan",
        verbose_name="سفارش",
    )

    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[
            MinValueValidator(
                Decimal("0.01"),
            ),
        ],
        verbose_name="مبلغ کل اقساط",
        help_text="مبلغ بر حسب تومان",
    )

    months = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
        ],
        verbose_name="تعداد اقساط",
        help_text="تعداد ماه‌های بازپرداخت",
    )

    monthly_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[
            MinValueValidator(
                Decimal("0.01"),
            ),
        ],
        verbose_name="مبلغ هر قسط",
        help_text="مبلغ هر قسط بر حسب تومان",
    )

    start_date = models.DateField(
        verbose_name="تاریخ شروع اقساط",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        verbose_name="وضعیت برنامه اقساط",
    )

    description = models.TextField(
        blank=True,
        default="",
        verbose_name="توضیحات",
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
        ordering = [
            "-created_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "status",
                    "start_date",
                ],
                name="installment_plan_status_idx",
            ),
        ]

        verbose_name = "برنامه اقساط"
        verbose_name_plural = "برنامه‌های اقساط"

    def __str__(self):
        return (
            f"اقساط سفارش "
            f"#{self.order_id}"
        )

    @property
    def paid_amount(self):
        """
        مجموع اقساط پرداخت‌شده.
        """

        return sum(
            (
                payment.amount
                for payment
                in self.installments.filter(
                    status=
                        InstallmentPayment.Status.PAID,
                )
            ),
            Decimal("0"),
        )

    @property
    def remaining_amount(self):
        """
        مبلغ باقی‌مانده اقساط.
        """

        remaining = (
            self.total_amount
            - self.paid_amount
        )

        return max(
            remaining,
            Decimal("0"),
        )


# =========================================================
# پرداخت هر قسط
# =========================================================
class InstallmentPayment(models.Model):
    """
    یکی از اقساط برنامه پرداخت سفارش.
    """

    class Status(models.TextChoices):
        PENDING = (
            "pending",
            "در انتظار پرداخت",
        )

        PAID = (
            "paid",
            "پرداخت‌شده",
        )

        OVERDUE = (
            "overdue",
            "سررسید گذشته",
        )

        CANCELLED = (
            "cancelled",
            "لغوشده",
        )

    plan = models.ForeignKey(
        InstallmentPlan,
        on_delete=models.CASCADE,
        related_name="installments",
        verbose_name="برنامه اقساط",
    )

    installment_number = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
        ],
        verbose_name="شماره قسط",
    )

    due_date = models.DateField(
        verbose_name="تاریخ سررسید",
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[
            MinValueValidator(
                Decimal("0.01"),
            ),
        ],
        verbose_name="مبلغ قسط",
        help_text="مبلغ بر حسب تومان",
    )

    late_fee = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0"),
        validators=[
            MinValueValidator(
                Decimal("0"),
            ),
        ],
        verbose_name="جریمه دیرکرد",
        help_text="مبلغ جریمه بر حسب تومان",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name="وضعیت قسط",
    )

    payment = models.OneToOneField(
        Payment,
        on_delete=models.SET_NULL,
        related_name="installment_payment",
        blank=True,
        null=True,
        verbose_name="تراکنش پرداخت",
    )

    paid_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="زمان پرداخت",
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
        ordering = [
            "installment_number",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "plan",
                    "installment_number",
                ],
                name=(
                    "unique_installment_number_per_plan"
                ),
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "status",
                    "due_date",
                ],
                name="installment_due_status_idx",
            ),
        ]

        verbose_name = "قسط"
        verbose_name_plural = "اقساط"

    def __str__(self):
        return (
            f"قسط {self.installment_number} "
            f"سفارش #{self.plan.order_id}"
        )

    @property
    def total_payable(self):
        """
        مبلغ کل قابل پرداخت شامل جریمه دیرکرد.
        """

        return (
            self.amount
            + self.late_fee
        )

    @property
    def is_paid(self):
        """
        سازگاری خواندنی با ساختار قبلی.
        """

        return (
            self.status
            == self.Status.PAID
        )

    def mark_paid(
        self,
        payment=None,
    ):
        """
        ثبت قسط به‌عنوان پرداخت‌شده.
        """

        self.status = self.Status.PAID
        self.paid_at = timezone.now()

        update_fields = [
            "status",
            "paid_at",
            "updated_at",
        ]

        if payment is not None:
            self.payment = payment

            update_fields.append(
                "payment",
            )

        self.save(
            update_fields=update_fields,
        )

        remaining_installments = (
            self.plan.installments
            .exclude(
                status=self.Status.PAID,
            )
            .exists()
        )

        if not remaining_installments:
            self.plan.status = (
                InstallmentPlan.Status.COMPLETED
            )

            self.plan.save(
                update_fields=[
                    "status",
                    "updated_at",
                ],
            )
