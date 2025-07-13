from django.db import models
from django.contrib.auth.models import User


class WatchedURL(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.URLField()
    product_name = models.CharField(max_length=255, blank=True, null=True)  # اضافه شده
    last_checked = models.DateTimeField(null=True, blank=True)
    last_price = models.BigIntegerField(null=True, blank=True)  # ✅ عدد صحیح ریالی بدون اعشار
    created_at = models.DateTimeField(auto_now_add=True)
  
    class Meta:
        unique_together = ('user', 'url')  # ✅ یکتا بودن آدرس برای هر کاربر

    def __str__(self):
        return self.url



class PriceHistory(models.Model):
    watched_url = models.ForeignKey(WatchedURL, on_delete=models.CASCADE, related_name='history')
    price = models.BigIntegerField()  # ✅ عدد صحیح ریالی بدون اعشار
    checked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.price} at {self.checked_at}"