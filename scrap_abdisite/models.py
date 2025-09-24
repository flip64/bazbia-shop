from django.db import models
from django.conf import settings
from products.models import ProductVariant
from suppliers.models import Supplier 


class WatchedURL(models.Model):
    """
    این مدل برای نگهداری لینک‌ها و قیمت‌های پایش شده محصولات در سایت‌های تأمین‌کننده است.
    هر رکورد نشان‌دهنده یک لینک از یک تأمین‌کننده برای یک محصول خاص است.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name='watched_urls',
        null=True
    )

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='watched_urls',
    )

    url = models.URLField(max_length=500)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_checked = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def product(self):
        """برگرداندن محصول از روی واریانت"""
        return self.variant.product if self.variant else None

    def __str__(self):
        product_name = self.product.name if self.product else "بدون محصول"
        return f"{product_name} | {self.supplier.name} | {self.price}"


class PriceHistory(models.Model):
    watched_url = models.ForeignKey(WatchedURL, on_delete=models.CASCADE, related_name='history')
    price = models.BigIntegerField()  # ✅ عدد صحیح ریالی بدون اعشار
    checked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.price} at {self.checked_at}"
