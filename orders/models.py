
from django.db import models
from django.conf import settings

# ================ضثف۱۲ثضفغاض۲  ۴۳۲ث==============
# مدل سفارش (Order)
# ==============================
from django.conf import settings
from django.db import models


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CANCELLED = "cancelled"
    STATUS_PAID = "paid"
    STATUS_SHIPPED = "shipped"
    STATUS_COMPLETED = "completed"

    STATUS_CHOICES = [
        (
            STATUS_PENDING,
            "در انتظار پرداخت"
        ),
        (
            STATUS_CANCELLED,
            "لغو شده"
        ),
        (
            STATUS_PAID,
            "پرداخت شده"
        ),
        (
            STATUS_SHIPPED,
            "ارسال شده"
        ),
        (
            STATUS_COMPLETED,
            "تحویل داده شده"
        ),
    ]

    PAYMENT_ONLINE = "online"
    PAYMENT_COD = "cod"

    PAYMENT_METHOD_CHOICES = [
        (
            PAYMENT_ONLINE,
            "پرداخت آنلاین"
        ),
        (
            PAYMENT_COD,
            "پرداخت در محل"
        ),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True
    )

    # آدرس اصلی انتخاب‌شده توسط مشتری
    shipping_address = models.ForeignKey(
        "customers.CustomerAddress",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders"
    )

    # نسخه ثابت آدرس در لحظه ثبت سفارش
    shipping_address_snapshot = models.JSONField(
        default=dict,
        blank=True
    )

    shipping_method_code = models.CharField(
        max_length=50,
        blank=True,
        default=""
    )

    shipping_method_title = models.CharField(
        max_length=100,
        blank=True,
        default=""
    )

    shipping_quote_id = models.CharField(
        max_length=100,
        blank=True,
        default=""
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default=PAYMENT_ONLINE
    )

    # تمام مبلغ‌ها در پروژه بازبیا به تومان هستند
    items_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="جمع مبلغ کالاها به تومان"
    )

    shipping_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="هزینه ارسال به تومان"
    )

    discount_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="مجموع تخفیف سفارش به تومان"
    )

    total_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="مبلغ نهایی قابل پرداخت به تومان"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "status"]
            ),
            models.Index(
                fields=["created_at"]
            ),
        ]

    def calculate_total_price(self):
        """
        محاسبه مبلغ قابل پرداخت سفارش.

        items_total + shipping_cost - discount_amount
        """
        total = (
            self.items_total
            + self.shipping_cost
            - self.discount_amount
        )

        return max(total, 0)

    def save(self, *args, **kwargs):
        self.total_price = (
            self.calculate_total_price()
        )

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"Order #{self.pk} - "
            f"{self.user}"
        )

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
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        null=True, blank=True, related_name='cart',
        help_text='اگر کاربر لاگین نکرده، این مقدار تهی می‌ماند.'
    )
    session_key = models.CharField(
        max_length=40, null=True, blank=True,
        help_text='برای کاربران مهمان، کلید سشن ذخیره می‌شود.'
         )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    is_active = models.BooleanField(default=True)
    
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
