from django.db import models

class Supplier(models.Model):
    """
    این مدل برای نگهداری اطلاعات تأمین‌کننده‌ها (فروشندگان عمده) است.
    """

    name = models.CharField(max_length=255, unique=True, verbose_name="نام تأمین‌کننده")
    website = models.URLField(blank=True, null=True, verbose_name="آدرس وب‌سایت")
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="شماره تماس")
    email = models.EmailField(blank=True, null=True, verbose_name="ایمیل")
    address = models.TextField(blank=True, null=True, verbose_name="آدرس")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")

    class Meta:
        ordering = ['name']
        verbose_name = "تأمین‌کننده"
        verbose_name_plural = "تأمین‌کنندگان"

    def __str__(self):
        return self.name
