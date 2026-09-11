from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from community.models import ProductQuestion
from community.api.serializers import ProductAnswerSerializer


class ProductAnswerCreateAPIView(generics.CreateAPIView):
    serializer_class = ProductAnswerSerializer
    permission_classes = [IsAuthenticated]

    def get_question(self):
        if not hasattr(self, "_question"):
            self._question = get_object_or_404(
                ProductQuestion.objects.select_related("product"),
                id=self.kwargs["question_id"],
                status=ProductQuestion.STATUS_APPROVED,
            )

        return self._question

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["question"] = self.get_question()
        return context