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
