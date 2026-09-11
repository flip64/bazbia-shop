from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from community.models import ProductAnswer, ProductReview
from community.services.helpful_vote_service import HelpfulVoteService


class ProductReviewHelpfulToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, review_id):
        review = get_object_or_404(
            ProductReview,
            id=review_id,
            status=ProductReview.STATUS_APPROVED,
        )

        try:
            helpful = HelpfulVoteService.toggle_review_vote(
                user=request.user,
                review=review,
            )

        except DjangoValidationError as exc:
            message = exc.messages[0] if exc.messages else str(exc)

            return Response(
                {"detail": message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            "helpful": helpful,
            "helpful_count": review.helpful_votes.count(),
        })


class ProductAnswerHelpfulToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, answer_id):
        answer = get_object_or_404(
            ProductAnswer,
            id=answer_id,
            status=ProductAnswer.STATUS_APPROVED,
        )

        try:
            helpful = HelpfulVoteService.toggle_answer_vote(
                user=request.user,
                answer=answer,
            )

        except DjangoValidationError as exc:
            message = exc.messages[0] if exc.messages else str(exc)

            return Response(
                {"detail": message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            "helpful": helpful,
            "helpful_count": answer.helpful_votes.count(),
        })