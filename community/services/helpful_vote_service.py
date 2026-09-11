from django.core.exceptions import ValidationError
from django.db import transaction

from community.models import AnswerHelpfulVote, ReviewHelpfulVote


class HelpfulVoteService:

    @staticmethod
    @transaction.atomic
    def toggle_review_vote(*, user, review) -> bool:
        if not user or not user.is_authenticated:
            raise ValidationError("برای ثبت رأی باید وارد حساب کاربری شوید.")

        if review.user_id == user.id:
            raise ValidationError("نمی‌توانید دیدگاه خودتان را مفید علامت بزنید.")

        vote = ReviewHelpfulVote.objects.filter(review=review, user=user).first()

        if vote:
            vote.delete()
            return False

        ReviewHelpfulVote.objects.create(review=review, user=user)
        return True

    @staticmethod
    @transaction.atomic
    def toggle_answer_vote(*, user, answer) -> bool:
        if not user or not user.is_authenticated:
            raise ValidationError("برای ثبت رأی باید وارد حساب کاربری شوید.")

        if answer.user_id == user.id:
            raise ValidationError("نمی‌توانید پاسخ خودتان را مفید علامت بزنید.")

        vote = AnswerHelpfulVote.objects.filter(answer=answer, user=user).first()

        if vote:
            vote.delete()
            return False

        AnswerHelpfulVote.objects.create(answer=answer, user=user)
        return True