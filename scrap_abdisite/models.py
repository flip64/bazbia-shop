from django.db import models
from django.contrib.auth.models import User
from django.db import models
from products.models import Product
from suppliers.models import Supplier 
from django.conf import settings

# ==============================
# مدل بررسی لینکها  = (WatchedURL)
# ==============================

class WatchedURL(models.Model):
    """
    این مدل برای نگهداری لینک‌ها و قیمت‌های پایش شده محصولات در سایت‌های تأمین‌کننده است.
    هر رکورد نشان‌دهنده یک لینک از یک تأمین‌کننده برای یک محصول خاص است.
    """
   
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # ارتباط با محصول فروشگاه شما (هر WatchedUrl به یک محصول وصل می‌شود)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='watched_urls' ,
        null=True  # از طریق product.watched_urls می‌توان به همه لینک‌ها دسترسی داشت
    )

    # ارتباط با تأمین‌کننده محصول (هر WatchedUrl به یک Supplier وصل می‌شود)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='watched_urls',
            # از طریق supplier.watched_urls می‌توان به همه لینک‌های آن تأمین‌کننده دسترسی داشت
    )

    # لینک صفحه محصول در سایت تأمین‌کننده
    url = models.URLField(max_length=500)

    # اخرین قیمت مشاهده شده در لینک تأمین‌کننده 
    price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0 , 
        blank=True,
        
    )

    # زمان ایجاد رکورد (زمانی که این لینک برای اولین بار پایش شده یا ثبت شده)
    created_at = models.DateTimeField(auto_now_add=True)

    # زمان آخرین باری که این لینک بررسی یا به‌روزرسانی شده
    last_checked = models.DateTimeField(auto_now=True)

    class Meta:
        # مرتب‌سازی پیش‌فرض: جدیدترین‌ها ابتدا
        ordering = ['-created_at']

    def __str__(self):
        # نمایش رشته‌ای خوانا از نام محصول، نام تأمین‌کننده و قیمت
        return f"{self.product.name} | {self.supplier.name} | {self.price}"



class PriceHistory(models.Model):
    watched_url = models.ForeignKey(WatchedURL, on_delete=models.CASCADE, related_name='history')
    price = models.BigIntegerField()  # ✅ عدد صحیح ریالی بدون اعشار
    checked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.price} at {self.checked_at}"
