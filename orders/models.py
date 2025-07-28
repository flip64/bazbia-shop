from django.db import models

from django.db import models
from django.conf import settings

# ==============================
# مدل سفارش (Order)
# ==============================
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت (رزرو)'),
        ('cancelled', 'لغو شده (آزاد شدن رزرو)'),
        ('paid', 'پرداخت شده'),
        ('shipped', 'ارسال شده'),
        ('completed', 'تحویل داده شده'),
        ('cancelled', 'لغو شده'),
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
