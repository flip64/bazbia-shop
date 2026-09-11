from django.urls import path

from community.api.views import (
    ProductReviewListCreateAPIView,
    ProductQuestionListCreateAPIView,
    ProductAnswerCreateAPIView,
)


app_name = "community_api"


urlpatterns = [
    # ==========================================
    # Reviews
    # ==========================================
    path(
        "products/<slug:slug>/reviews/",
        ProductReviewListCreateAPIView.as_view(),
        name="product-reviews",
    ),

    # ==========================================
    # Questions
    # ==========================================
    path(
        "products/<slug:slug>/questions/",
        ProductQuestionListCreateAPIView.as_view(),
        name="product-questions",
    ),

    # ==========================================
    # Answers
    # ==========================================
    path(
        "questions/<int:question_id>/answers/",
        ProductAnswerCreateAPIView.as_view(),
        name="question-answers",
    ),
]