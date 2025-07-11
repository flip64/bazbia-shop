from django.db import models
from orders.models import Order

# ==============================
# مدل پرداخت (Payment)
# ==============================
class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('online', 'پرداخت آنلاین'),
        ('cod', 'پرداخت در محل'),
        ('card_to_card', 'کارت به کارت'),
        ('wallet', 'کیف پول داخلی'),
        ('check', 'چک / سفته (برای اقساط)'),
    ]

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name='payments'
    )

    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='مبلغ پرداخت شده'
    )

    payment_method = models.CharField(
        max_length=30, choices=PAYMENT_METHOD_CHOICES
    )

    tracking_code = models.CharField(
        max_length=100, blank=True, null=True,
        help_text='کد پیگیری درگاه یا شماره فیش کارت به کارت'
    )

    proof_image = models.ImageField(
        upload_to='payment_proofs/', blank=True, null=True,
        help_text='تصویر رسید کارت به کارت'
    )

    is_successful = models.BooleanField(
        default=True, help_text='آیا پرداخت موفق بوده؟'
    )

    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.amount} for Order #{self.order.id}"



# ==============================
# برنامه اقساط سفارش (InstallmentPlan)
# ==============================
class InstallmentPlan(models.Model):
    order = models.OneToOneField(
        'orders.Order', on_delete=models.CASCADE,
        related_name='installment_plan'
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    months = models.PositiveIntegerField(help_text="تعداد ماه‌های پرداخت")
    monthly_amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"اقساط سفارش #{self.order.id}"


# ==============================
# پرداخت هر قسط (InstallmentPayment)
# ==============================
class InstallmentPayment(models.Model):
    plan = models.ForeignKey(
        InstallmentPlan, on_delete=models.CASCADE,
        related_name='payments'
    )
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(blank=True, null=True)

    # جریمه دیرکرد
    late_fee = models.DecimalField(
        max_digits=12, decimal_places=2,
        default=0, help_text='مقدار جریمه دیرکرد (در صورت وجود)'
    )

    def __str__(self):
        return f"قسط {self.due_date} - سفارش #{self.plan.order.id}"
