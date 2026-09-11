from django.conf import settings
from django.db import models

from .question import ProductQuestion


class ProductAnswer(models.Model):
    """پاسخ کاربر یا بازبیا به یک سؤال محصول."""

    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_PENDING, "در انتظار تأیید"),
        (STATUS_APPROVED, "تأیید شده"),
        (STATUS_REJECTED, "رد شده"),
    ]

    question = models.ForeignKey(ProductQuestion, on_delete=models.CASCADE, related_name="answers")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="product_answers")

    body = models.TextField()

    is_verified_purchase = models.BooleanField(default=False, editable=False)
    is_official = models.BooleanField(default=False, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - question #{self.question_id}"