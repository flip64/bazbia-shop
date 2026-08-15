from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class Purchase(models.Model):
    """
    خرید واقعی کالا برای ورود به انبار داخلی بازبیا.
    """

    STATUS_DRAFT = "draft"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = (
        (
            STATUS_DRAFT,
            "پیش‌نویس",
        ),
        (
            STATUS_CONFIRMED,
            "تأیید شده",
        ),
        (
            STATUS_CANCELLED,
            "لغو شده",
        ),
    )

    PAYMENT_CASH = "cash"
    PAYMENT_CREDIT = "credit"

    PAYMENT_CHOICES = (
        (
            PAYMENT_CASH,
            "نقدی",
        ),
        (
            PAYMENT_CREDIT,
            "نسیه",
        ),
    )

    supplier = models.ForeignKey(
        "suppliers.Supplier",
        on_delete=models.PROTECT,
        related_name="purchases",
        verbose_name="تأمین‌کننده",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        verbose_name="وضعیت",
    )

    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default=PAYMENT_CREDIT,
        verbose_name="نوع پرداخت",
    )

    invoice_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="شماره فاکتور",
    )

    note = models.TextField(
        blank=True,
        verbose_name="یادداشت",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد",
    )

    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاریخ تأیید",
    )

    class Meta:
        ordering = [
            "-created_at",
            "-id",
        ]

        verbose_name = "خرید"
        verbose_name_plural = "خریدها"

    def __str__(self):
        return (
            f"خرید #{self.pk} - "
            f"{self.supplier}"
        )

    @property
    def total_amount(self) -> Decimal:
        """
        محاسبه جمع مبلغ تمام ردیف‌های خرید.
        """

        total = Decimal("0")

        for item in self.items.all():
            total += item.total_amount

        return total


class PurchaseItem(models.Model):
    """
    یک ردیف از فاکتور خرید.

    هر PurchaseItem بعد از تأیید Purchase
    به یک InventoryLot تبدیل می‌شود.
    """

    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="خرید",
    )

    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.PROTECT,
        related_name="purchase_items",
        verbose_name="واریانت",
    )

    quantity = models.PositiveIntegerField(
        verbose_name="تعداد",
    )

    unit_cost = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        verbose_name="قیمت خرید هر واحد",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد",
    )

    class Meta:
        ordering = [
            "id",
        ]

        verbose_name = "آیتم خرید"
        verbose_name_plural = "آیتم‌های خرید"

    def __str__(self):
        return (
            f"{self.variant} × "
            f"{self.quantity}"
        )

    @property
    def total_amount(self) -> Decimal:
        """
        محاسبه جمع مبلغ این ردیف خرید.
        """

        return (
            Decimal(self.quantity)
            * Decimal(str(self.unit_cost))
        )

    def clean(self):
        """
        اعتبارسنجی تعداد و قیمت خرید.

        بررسی None برای سازگاری با ردیف‌های خالی
        فرم Inline پنل مدیریت ضروری است.
        """

        super().clean()

        if (
            self.quantity is not None
            and self.quantity <= 0
        ):
            raise ValidationError(
                {
                    "quantity": (
                        "تعداد باید بزرگ‌تر از صفر باشد."
                    ),
                }
            )

        if (
            self.unit_cost is not None
            and self.unit_cost <= 0
        ):
            raise ValidationError(
                {
                    "unit_cost": (
                        "قیمت خرید باید بزرگ‌تر از صفر باشد."
                    ),
                }
            )
