from django.db import models

# ==============================
# 📦 مدل حرکات موجودی انبار (Inventory Movement)
# ==============================
class InventoryMovement(models.Model):
    MOVEMENT_TYPE_CHOICES = [
        ('purchase', 'ورود کالا از تامین‌کننده'),
        ('reserve', 'رزرو موقت برای سفارش'),
        ('sale', 'فروش قطعی و خروج کالا'),
        ('cancel', 'لغو سفارش و برگشت رزرو'),
        ('return', 'مرجوعی از سمت مشتری'),
        ('adjustment', 'اصلاح دستی موجودی توسط مدیر انبار'),
    ]

    # ارتباط با محصول دقیق (Variant)
    product_variant = models.ForeignKey(
        'products.ProductVariant', on_delete=models.CASCADE,
        related_name='inventory_movements'
    )

    # نوع حرکت انبار (ورود، رزرو، فروش و ...)
    type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPE_CHOICES
    )

    # تعداد تغییر (ممکن است مثبت یا منفی)
    quantity = models.IntegerField(
        help_text='تعداد مثبت یا منفی تغییر یافته در موجودی'
    )

    # در صورت وجود، این حرکت به سفارش خاصی مربوط می‌شود
    related_order = models.ForeignKey(
        'orders.Order', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='inventory_movements'
    )

    # زمان ثبت این حرکت
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product_variant} - {self.type} ({self.quantity})"

    class Meta:
        verbose_name = "حرکت موجودی"
        verbose_name_plural = "حرکات موجودی"


class InventoryLot(models.Model):
    """
    یک بچ/لات موجودی داخلی با بهای خرید مشخص.

    هر بار کالایی برای انبار بازبیا خریداری می‌شود،
    یک InventoryLot جدید ایجاد می‌کنیم.
    """

    product_variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.PROTECT,
        related_name="inventory_lots",
        verbose_name="واریانت",
    )

    supplier = models.ForeignKey(
        "suppliers.Supplier",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_lots",
        verbose_name="تأمین‌کننده",
    )

    purchase_item = models.OneToOneField(
        "purchases.PurchaseItem",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="inventory_lot",
        verbose_name="ردیف خرید",
        help_text=(
            "ردیف فاکتور خریدی که این لات از آن ایجاد شده است. "
            "برای موجودی‌های اولیه و اصلاحات می‌تواند خالی باشد."
        ),
    )

    quantity_received = models.PositiveIntegerField(
        verbose_name="تعداد اولیه",
    )

    quantity_remaining = models.PositiveIntegerField(
        verbose_name="تعداد باقی‌مانده",
    )

    unit_cost = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        verbose_name="بهای خرید هر واحد",
    )

    received_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ورود",
    )

    note = models.TextField(
        blank=True,
        verbose_name="یادداشت",
    )

    class Meta:
        ordering = [
            "received_at",
            "id",
        ]

        verbose_name = "لات موجودی"
        verbose_name_plural = "لات‌های موجودی"

        indexes = [
            models.Index(
                fields=[
                    "product_variant",
                    "quantity_remaining",
                ]
            )
        ]

    @property
    def remaining_value(self):
        return (
            self.quantity_remaining
            * self.unit_cost
        )

    def __str__(self):
        return (
            f"{self.product_variant} | "
            f"{self.quantity_remaining}/"
            f"{self.quantity_received} | "
            f"{self.unit_cost}"
        )
