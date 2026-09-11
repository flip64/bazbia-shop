from django.conf import settings
from django.db import models

from .answer import ProductAnswer
from .review import ProductReview


class ReviewHelpfulVote(models.Model):
    review = models.ForeignKey(ProductReview, on_delete=models.CASCADE, related_name="helpful_votes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="review_helpful_votes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["review", "user"], name="unique_review_helpful_vote"),
        ]

    def __str__(self):
        return f"{self.user} -> review #{self.review_id}"


class AnswerHelpfulVote(models.Model):
    answer = models.ForeignKey(ProductAnswer, on_delete=models.CASCADE, related_name="helpful_votes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="answer_helpful_votes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["answer", "user"], name="unique_answer_helpful_vote"),
        ]

    def __str__(self):
        return f"{self.user} -> answer #{self.answer_id}"