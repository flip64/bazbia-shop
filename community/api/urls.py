from django.urls import path

from community.api.views import ProductAnswerCreateAPIView, ProductAnswerHelpfulToggleAPIView, ProductQuestionListCreateAPIView, ProductReviewHelpfulToggleAPIView, ProductReviewListCreateAPIView


app_name = "community_api"


urlpatterns = [
    path("products/<slug:slug>/reviews/", ProductReviewListCreateAPIView.as_view(), name="product-reviews"),
    path("products/<slug:slug>/questions/", ProductQuestionListCreateAPIView.as_view(), name="product-questions"),
    path("questions/<int:question_id>/answers/", ProductAnswerCreateAPIView.as_view(), name="question-answers"),

    path("reviews/<int:review_id>/helpful/", ProductReviewHelpfulToggleAPIView.as_view(), name="review-helpful"),
    path("answers/<int:answer_id>/helpful/", ProductAnswerHelpfulToggleAPIView.as_view(), name="answer-helpful"),
]