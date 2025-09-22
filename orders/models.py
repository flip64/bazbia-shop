
from django.db import models
from django.conf import settings

# ================ضثف۱۲ثضفغاض۲  ۴۳۲ث==============
# مدل سفارش (Order)
# ==============================
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت (رزرو)'),
        ('cancelled', 'لغو شده (آزاد شدن رزرو)'),
        ('paid', 'پرداخت شده'),
        ('shipped', 'ارسال شده'),
        ('completed', 'تحویل داده شده'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='orders'
    )

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='pending'
    )

    total_price = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='جمع کل سفارش پس از تخفیف'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user}"


# ==============================
# مدل آیتم‌های سفارش (OrderItem)
# ==============================
class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name='items'
    )

    variant = models.ForeignKey(
        'products.ProductVariant', on_delete=models.CASCADE,
        related_name='order_items'
    )

    quantity = models.PositiveIntegerField(default=1)

    price = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='قیمت نهایی هر آیتم در لحظه خرید'
    )

    def __str__(self):
        return f"{self.variant} x {self.quantity} (Order #{self.order.id})"





# ==============================
# مدل سبد خرید (Cart)
# ==============================
class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        null=True, blank=True, related_name='carts',
        help_text='اگر کاربر لاگین نکرده، این مقدار تهی می‌ماند.'
    )
    session_key = models.CharField(
        max_length=40, null=True, blank=True,
        help_text='برای کاربران مهمان، کلید سشن ذخیره می‌شود.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_empty(self):
        return not self.items.exists()

    def total_price(self):
        return sum(item.total_price() for item in self.items.all())

    def __str__(self):
        if self.user:
            return f"Cart (User: {self.user})"
        return f"Cart (Session: {self.session_key})"

# ==============================
# آیتم‌های سبد خرید (CartItem)
# ==============================
class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE,
        related_name='items'
    )
    variant = models.ForeignKey(
        'products.ProductVariant', on_delete=models.CASCADE,
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def price(self):
        return self.variant.price  # فرض بر این است که فیلد قیمت در مدل ProductVariant وجود دارد

    def total_price(self):
        return self.price() * self.quantity

    def __str__(self):
        return f"{self.variant} x {self.quantity}"




# ==============================
#. مدل خلاصه گزارش. فروش (SalesSummery)
# ==============================
from django.db import models

class SalesSummary(models.Model):
    """
    جدول خلاصه گزارش فروش محصولات.
    هر رکورد نشان‌دهنده جمع فروش یک محصول در یک بازه زمانی مشخص است.
    """
    
    # محصول مربوط به رکورد
    product = models.ForeignKey(
        'products.product',
        on_delete=models.CASCADE,
        related_name='sales_summary',
        help_text='محصولی که این رکورد خلاصه فروش آن است'
    )

    # اگر محصول دارای واریانت باشد (مثلاً رنگ یا سایز)، مشخص می‌کند
    variant = models.ForeignKey(
        'products.productvariant',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='sales_summary',
        help_text='واریانت محصول، اگر وجود داشته باشد'
    )

    # بازه زمانی خلاصه
    period_start = models.DateField(help_text='تاریخ شروع بازه')
    period_end = models.DateField(help_text='تاریخ پایان بازه')

    # تعداد کل فروش در این بازه
    total_quantity = models.PositiveIntegerField(default=0, help_text='جمع تعداد فروش در بازه')

    # مجموع مبلغ فروش در این بازه
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text='جمع مبلغ فروش در بازه')

    # تاریخ ایجاد رکورد
    created_at = models.DateTimeField(auto_now_add=True)

    # آخرین بروزرسانی رکورد
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'variant', 'period_start', 'period_end')
        indexes = [
            models.Index(fields=['product', 'period_start']),
            models.Index(fields=['period_start']),
        ]

    def __str__(self):
        return f"{self.product.name} ({self.variant}) : {self.total_quantity} sold from {self.period_start} to {self.period_end}"
