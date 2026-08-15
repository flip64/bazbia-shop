from django.db import models


# ==============================
# 📦 مدل حرکات موجودی انبار
# ==============================
class InventoryMovement(models.Model):
    MOVEMENT_TYPE_CHOICES = [
        (
            "purchase",
            "ورود کالا از تأمین‌کننده",
        ),
        (
            "reserve",
            "رزرو موقت برای سفارش",
        ),
        (
            "sale",
            "فروش قطعی و خروج کالا",
        ),
        (
            "cancel",
            "لغو سفارش و برگشت رزرو",
        ),
        (
            "return",
            "مرجوعی از سمت مشتری",
        ),
        (
            "adjustment",
            "اصلاح دستی موجودی توسط مدیر انبار",
        ),
    ]

    product_variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.CASCADE,
        related_name="inventory_movements",
        verbose_name="واریانت",
    )

    type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPE_CHOICES,
        verbose_name="نوع حرکت",
    )

    quantity = models.IntegerField(
        verbose_name="تعداد",
        help_text=(
            "تعداد مثبت یا منفی تغییر یافته "
            "در موجودی"
        ),
    )

    related_order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_movements",
        verbose_name="سفارش مرتبط",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ثبت",
    )

    class Meta:
        ordering = [
            "-created_at",
            "-id",
        ]

        verbose_name = "حرکت موجودی"
        verbose_name_plural = "حرکات موجودی"

    def __str__(self):
        return (
            f"{self.product_variant} - "
            f"{self.get_type_display()} "
            f"({self.quantity})"
        )


# ==============================
# 📦 مدل لات موجودی
# ==============================
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
            "ردیف فاکتور خریدی که این لات "
            "از آن ایجاد شده است. برای موجودی‌های "
            "قدیمی و اصلاحات دستی می‌تواند خالی باشد."
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
                ],
            ),
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
