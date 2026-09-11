from django.core.exceptions import ValidationError
from django.db import transaction

from community.models import ProductAnswer, ProductQuestion
from community.services.purchase_verification_service import (
    PurchaseVerificationService,
)


class AnswerService:
    """
    سرویس ثبت پاسخ به پرسش‌های محصولات.
    """

    @classmethod
    @transaction.atomic
    def create_answer(
        cls,
        *,
        user,
        question: ProductQuestion,
        body,
    ) -> ProductAnswer:
        """
        ثبت پاسخ کاربر برای یک سؤال.
        """

        if not user or not user.is_authenticated:
            raise ValidationError(
                "برای ثبت پاسخ باید وارد حساب کاربری شوید."
            )

        product = question.product

        is_verified_purchase = (
            PurchaseVerificationService.has_user_purchased_product(
                user=user,
                product=product,
            )
        )

        is_official = bool(
            user.is_staff or user.is_superuser
        )

        answer = ProductAnswer.objects.create(
            question=question,
            user=user,
            body=body,
            is_verified_purchase=is_verified_purchase,
            is_official=is_official,
            status=ProductAnswer.STATUS_PENDING,
        )

        return answer