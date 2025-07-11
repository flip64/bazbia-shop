from django.db import models
from django.db import models
from django.contrib.auth.models import User

# ==============================
# مدل سطح مشتری (CustomerLevel)
# ==============================
class CustomerLevel(models.Model):
    name = models.CharField(max_length=50)
    # سقف اعتبار این سطح
    max_credit = models.DecimalField(max_digits=12, decimal_places=2)
    # درصد سود ماهانه این سطح
    benefit_percent = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text='سود ماهانه به درصد'
    )

    def __str__(self):
        return self.name




# ==============================
# مدل مشتری (Customer)
# ==============================
class Customer(models.Model):
    # ارتباط یک‌به‌یک با یوزر جنگو
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='customer_profile'
    )

    # اطلاعات تکمیلی مشتری
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    # سطح مشتری ()
    level = models.ForeignKey(
        CustomerLevel, on_delete=models.SET_NULL,
        null=True, blank=True
    )

    # سقف اعتبار فعلی مشتری
    credit_limit = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )

    # آیا این مشتری در لیست سیاه است؟
    is_blacklisted = models.BooleanField(default=False)
    # آیا این مشتری در لیست مراقبتی (watchlist) است؟
    is_watchlisted = models.BooleanField(default=False)

    # زمان ثبت این پروفایل
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} Profile"

# ==============================
# مدل تضمین‌های مشتری (CustomerGuarantee)
# ==============================
class CustomerGuarantee(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE,
        related_name='guarantees'
    )

    # نوع تضمین: چک، سفته یا ضمانت‌نامه
    type = models.CharField(
        max_length=50,
        choices=[
            ('چک', 'چک'),
            ('سفته', 'سفته'),
            ('ضمانت‌نامه', 'ضمانت‌نامه')
        ]
    )

    # مبلغ تضمین
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    # توضیحات تکمیلی (مثلا شماره چک یا بانک)
    details = models.TextField(blank=True, null=True)

    # زمان ثبت این تضمین
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.user.username} - {self.type}"
