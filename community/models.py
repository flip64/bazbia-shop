from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from products.models import Product


class ProductReview(models.Model):
    """
    دیدگاه و امتیاز کاربر برای یک محصول.
    """

    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_PENDING, "در انتظار تأیید"),
        (STATUS_APPROVED, "تأیید شده"),
        (STATUS_REJECTED, "رد شده"),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="product_reviews",
    )

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
    )

    title = models.CharField(
        max_length=200,
        blank=True,
    )

    body = models.TextField()

    is_verified_purchase = models.BooleanField(
        default=False,
        editable=False,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["product", "user"],
                name="unique_product_review_per_user",
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.product} - {self.rating}"


class ProductQuestion(models.Model):
    """
    سؤال کاربر درباره یک محصول.
    """

    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_PENDING, "در انتظار تأیید"),
        (STATUS_APPROVED, "تأیید شده"),
        (STATUS_REJECTED, "رد شده"),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="questions",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="product_questions",
    )

    body = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.product}"


class ProductAnswer(models.Model):
    """
    پاسخ کاربر یا بازبیا به یک سؤال محصول.
    """

    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_PENDING, "در انتظار تأیید"),
        (STATUS_APPROVED, "تأیید شده"),
        (STATUS_REJECTED, "رد شده"),
    ]

    question = models.ForeignKey(
        ProductQuestion,
        on_delete=models.CASCADE,
        related_name="answers",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="product_answers",
    )

    body = models.TextField()

    is_verified_purchase = models.BooleanField(
        default=False,
        editable=False,
    )

    is_official = models.BooleanField(
        default=False,
        editable=False,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - question #{self.question_id}"