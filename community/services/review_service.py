from django.core.exceptions import ValidationError
from django.db import transaction

from community.models import ProductReview
from community.services.purchase_verification_service import (
    PurchaseVerificationService,
)


class ReviewService:
    """
    سرویس ثبت دیدگاه محصول.
    """

    @classmethod
    @transaction.atomic
    def create_review(
        cls,
        *,
        user,
        product,
        rating,
        body,
        title="",
    ) -> ProductReview:
        """
        ثبت یک دیدگاه جدید برای محصول.

        هر کاربر برای هر محصول فقط یک دیدگاه می‌تواند داشته باشد.
        """

        if not user or not user.is_authenticated:
            raise ValidationError(
                "برای ثبت دیدگاه باید وارد حساب کاربری شوید."
            )

        if ProductReview.objects.filter(
            user=user,
            product=product,
        ).exists():
            raise ValidationError(
                "شما قبلاً برای این محصول دیدگاه ثبت کرده‌اید."
            )

        is_verified_purchase = (
            PurchaseVerificationService.has_user_purchased_product(
                user=user,
                product=product,
            )
        )

        review = ProductReview.objects.create(
            user=user,
            product=product,
            rating=rating,
            title=title,
            body=body,
            is_verified_purchase=is_verified_purchase,
            status=ProductReview.STATUS_PENDING,
        )

        return review