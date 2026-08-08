from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from analytics.models import SiteEvent
from analytics.api.serializers import SiteEventCreateSerializer


def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR", "")


class SiteEventCreateAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SiteEventCreateSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        session_key = ""

        if hasattr(request, "session"):
            if not request.session.session_key:
                request.session.create()

            session_key = (
                request.session.session_key or ""
            )

        user = None

        if (
            request.user
            and request.user.is_authenticated
        ):
            user = request.user

        ip_address = get_client_ip(request)

        event = serializer.save(
            user=user,
            session_key=session_key,
            ip_hash=SiteEvent.hash_ip(ip_address),
            user_agent=request.META.get(
                "HTTP_USER_AGENT",
                "",
            )[:2000],
        )

        return Response(
            {
                "success": True,
                "event_id": event.pk,
            },
            status=status.HTTP_201_CREATED,
        )
