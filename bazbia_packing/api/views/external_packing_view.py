from django.conf import settings

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from bazbia_packing.api.serializers import (
    ExternalPackingRequestSerializer,
)


class ExternalPackingAPIView(APIView):
    """
    API عمومی موتور بسته‌بندی برای سرویس‌های خارجی.

    این endpoint فعلاً غیرفعال است و تا زمان تکمیل
    موتور بسته‌بندی و احراز هویت API Key، پاسخ 503 می‌دهد.
    """

    permission_classes = [
        permissions.AllowAny,
    ]

    def post(self, request):
        serializer = ExternalPackingRequestSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        is_enabled = getattr(
            settings,
            "BAZBIA_EXTERNAL_PACKING_API_ENABLED",
            False,
        )

        if not is_enabled:
            return Response(
                {
                    "detail": (
                        "سرویس عمومی بسته‌بندی "
                        "در حال حاضر غیرفعال است."
                    ),
                    "code": "external_packing_disabled",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "detail": (
                    "موتور عمومی بسته‌بندی "
                    "هنوز پیاده‌سازی نشده است."
                ),
                "code": "packing_engine_not_ready",
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
