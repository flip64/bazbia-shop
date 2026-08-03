from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from contact.api.serializers import (
    ContactMessageCreateSerializer,
)


def get_client_ip(request):
    forwarded_for = request.META.get(
        "HTTP_X_FORWARDED_FOR",
        "",
    )

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


class ContactMessageCreateAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = ContactMessageCreateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = None

        if (
            request.user
            and request.user.is_authenticated
        ):
            user = request.user

        contact_message = serializer.save(
            user=user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get(
                "HTTP_USER_AGENT",
                "",
            )[:500],
        )

        return Response(
            {
                "success": True,
                "message": (
                    "پیام شما با موفقیت ثبت شد. "
                    "همکاران ما به‌زودی با شما تماس می‌گیرند."
                ),
                "data": {
                    "id": contact_message.id,
                    "created_at": (
                        contact_message.created_at
                    ),
                },
            },
            status=status.HTTP_201_CREATED,
        )
