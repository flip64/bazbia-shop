from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid




# ==============================
# مدل سطح مشتری (CustomerLevel)
# ==============================
class CustomerLevel(models.Model):
    name = models.CharField(max_length=50)
    max_credit = models.DecimalField(max_digits=12, decimal_places=2)
    benefit_percent = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text='سود ماهانه به درصد'
    )

    def __str__(self):
        return self.name


# ==============================
# مدل مشتری (Customer)
# =============================

class Customer(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )

    phone = models.CharField(
        max_length=11,
        unique=True,
        db_index=True,
        blank=True,
        null=True,
        verbose_name="شماره موبایل",
    )

    level = models.ForeignKey(
        CustomerLevel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    avatar = models.ImageField(
        upload_to="avatar/",
        help_text="مسیر ذخیره تصویر در media",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.phone == "":
            self.phone = None

        super().save(*args, **kwargs)

    def __str__(self):
        return self.phone or self.user.username

# ==============================
# مدل تضمین‌های مشتری (CustomerGuarantee)
# ==============================
class CustomerGuarantee(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE,
        related_name='guarantees'
    )

    type = models.CharField(
        max_length=50,
        choices=[
            ('چک', 'چک'),
            ('سفته', 'سفته'),
            ('ضمانت‌نامه', 'ضمانت‌نامه')
        ]
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.user.username} - {self.type}"


# ==============================
# مدل انواع وضعیت‌ها (Status)
# ==============================
class Status(models.Model):
    code = models.CharField(max_length=30, unique=True)
    title = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title


# ==============================
# مدل وضعیت ترکیبی مشتری (CustomerState)
# ==============================
class CustomerState(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE)
    statuses = models.ManyToManyField(Status, related_name='customers')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.customer.user.username} → {[s.title for s in self.statuses.all()]}"


# ==============================
# مدل آدرس‌های مشتری (CustomerAddress)
# ==============================
class CustomerAddress(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE,
        related_name='addresses'
    )
    title = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField()
    city = models.CharField(max_length=50, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.customer.user.username} - {self.title or 'بدون عنوان'}"




# ==============================
# مدل کد تایید  مشتری (OTP)
# ==============================
class OTP(models.Model):
    MAX_ATTEMPTS = 5

    class Purpose(models.TextChoices):
        LOGIN = "login", "ورود"
        SET_PASSWORD = "set_password", "تنظیم رمز"
        VERIFY_PHONE = "verify_phone", "تأیید شماره موبایل"

    phone = models.CharField(
        max_length=11,
        db_index=True,
        verbose_name="شماره موبایل",
    )

    code_hash = models.CharField(
        max_length=128,
        verbose_name="هش کد تأیید",
    )

    purpose = models.CharField(
        max_length=20,
        choices=Purpose.choices,
        default=Purpose.LOGIN,
        verbose_name="هدف",
    )

    session_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    expires_at = models.DateTimeField(
        verbose_name="زمان انقضا",
    )

    attempts = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="تعداد تلاش",
    )

    is_used = models.BooleanField(
        default=False,
        verbose_name="استفاده شده",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    verified_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["phone", "purpose", "is_used"],
                name="otp_phone_purpose_used_idx",
            ),
        ]

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def has_exceeded_attempts(self):
        return self.attempts >= self.MAX_ATTEMPTS

    @property
    def is_valid(self):
        return (
            not self.is_used
            and not self.is_expired
            and not self.has_exceeded_attempts
        )

    def mark_as_used(self):
        self.is_used = True
        self.verified_at = timezone.now()

        self.save(
            update_fields=[
                "is_used",
                "verified_at",
            ]
        )

    def __str__(self):
        return f"{self.phone} - {self.get_purpose_display()}"