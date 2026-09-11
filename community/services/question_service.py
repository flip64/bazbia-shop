from django.core.exceptions import ValidationError
from django.db import transaction

from community.models import ProductQuestion


class QuestionService:
    """
    سرویس ثبت پرسش درباره محصول.
    """

    @classmethod
    @transaction.atomic
    def create_question(
        cls,
        *,
        user,
        product,
        body,
    ) -> ProductQuestion:
        """
        ثبت یک سؤال جدید برای محصول.
        """

        if not user or not user.is_authenticated:
            raise ValidationError(
                "برای ثبت پرسش باید وارد حساب کاربری شوید."
            )

        body = (body or "").strip()

        if not body:
            raise ValidationError(
                "متن پرسش نمی‌تواند خالی باشد."
            )

        question = ProductQuestion.objects.create(
            user=user,
            product=product,
            body=body,
            status=ProductQuestion.STATUS_PENDING,
        )

        return question
    