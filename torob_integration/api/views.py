import time

from django.db import DatabaseError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from torob_integration.models import TorobRequestLog
from torob_integration.services import (
    TorobProductSelector,
    TorobResponseBuilder,
)

from .authentication import TorobJWTAuthentication
from .serializers import TorobRequestSerializer


class TorobProductsAPIView(APIView):
    """
    endpoint اصلی TorobAPI نسخه ۳.

    حالت‌های ورودی:

    1. صفحه‌بندی:
        {
            "page": 1,
            "sort": "date_added_desc"
        }

    2. دریافت با شناسه:
        {
            "page_uniques": ["1695", "1696"]
        }

    3. دریافت با لینک:
        {
            "page_urls": [
                "https://bazbia.ir/product/example/?variant=1695"
            ]
        }
    """

    authentication_classes = [
        TorobJWTAuthentication,
    ]

    permission_classes = []

    def post(self, request, *args, **kwargs):
        started_at = time.perf_counter()

        log_data = self.build_initial_log_data(request)

        serializer = TorobRequestSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            error_message = self.extract_error_message(
                serializer.errors
            )

            duration_ms = self.calculate_duration_ms(
                started_at
            )

            log_data.update(
                {
                    "request_type": (
                        TorobRequestLog.RequestType.INVALID
                    ),
                    "response_status": (
                        status.HTTP_400_BAD_REQUEST
                    ),
                    "error_message": error_message,
                    "duration_ms": duration_ms,
                }
            )

            self.create_log_safely(log_data)

            return Response(
                {
                    "error": error_message,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = serializer.validated_data
        request_mode = serializer.request_mode

        try:
            if request_mode == "pagination":
                response_data = self.handle_pagination(
                    request=request,
                    validated_data=validated_data,
                )

                log_data.update(
                    {
                        "request_type": (
                            TorobRequestLog
                            .RequestType
                            .PAGINATION
                        ),
                        "page": validated_data["page"],
                        "sort": validated_data["sort"],
                    }
                )

            elif request_mode == "page_uniques":
                response_data = self.handle_page_uniques(
                    request=request,
                    validated_data=validated_data,
                )

                log_data.update(
                    {
                        "request_type": (
                            TorobRequestLog
                            .RequestType
                            .PAGE_UNIQUES
                        ),
                        "requested_items_count": len(
                            validated_data[
                                "page_uniques"
                            ]
                        ),
                    }
                )

            elif request_mode == "page_urls":
                response_data = self.handle_page_urls(
                    request=request,
                    validated_data=validated_data,
                )

                log_data.update(
                    {
                        "request_type": (
                            TorobRequestLog
                            .RequestType
                            .PAGE_URLS
                        ),
                        "requested_items_count": len(
                            validated_data[
                                "page_urls"
                            ]
                        ),
                    }
                )

            else:
                raise ValueError(
                    "Unsupported request mode."
                )

            duration_ms = self.calculate_duration_ms(
                started_at
            )

            products = response_data.get(
                "products",
                [],
            )

            log_data.update(
                {
                    "response_status": status.HTTP_200_OK,
                    "products_count": len(products),
                    "total_products": response_data.get(
                        "total",
                        0,
                    ),
                    "max_pages": response_data.get(
                        "max_pages",
                    ),
                    "duration_ms": duration_ms,
                }
            )

            self.create_log_safely(log_data)

            return Response(
                response_data,
                status=status.HTTP_200_OK,
            )

        except ValueError as exc:
            error_message = str(exc)

            duration_ms = self.calculate_duration_ms(
                started_at
            )

            log_data.update(
                {
                    "request_type": (
                        log_data.get("request_type")
                        or TorobRequestLog
                        .RequestType
                        .INVALID
                    ),
                    "response_status": (
                        status.HTTP_400_BAD_REQUEST
                    ),
                    "error_message": error_message,
                    "duration_ms": duration_ms,
                }
            )

            self.create_log_safely(log_data)

            return Response(
                {
                    "error": error_message,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except DatabaseError:
            error_message = (
                "Database error occurred while "
                "processing the request."
            )

            duration_ms = self.calculate_duration_ms(
                started_at
            )

            log_data.update(
                {
                    "response_status": (
                        status.HTTP_500_INTERNAL_SERVER_ERROR
                    ),
                    "error_message": error_message,
                    "duration_ms": duration_ms,
                }
            )

            self.create_log_safely(log_data)

            return Response(
                {
                    "error": error_message,
                },
                status=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
            )

        except Exception:
            error_message = (
                "An unexpected error occurred while "
                "processing the request."
            )

            duration_ms = self.calculate_duration_ms(
                started_at
            )

            log_data.update(
                {
                    "response_status": (
                        status.HTTP_500_INTERNAL_SERVER_ERROR
                    ),
                    "error_message": error_message,
                    "duration_ms": duration_ms,
                }
            )

            self.create_log_safely(log_data)

            return Response(
                {
                    "error": error_message,
                },
                status=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
            )

    @staticmethod
    def handle_pagination(
        *,
        request,
        validated_data,
    ) -> dict:
        """
        دریافت یک صفحه از محصولات با ترتیب مشخص.
        """

        page = validated_data["page"]
        sort = validated_data["sort"]

        variants, total = (
            TorobProductSelector.get_paginated(
                page=page,
                sort=sort,
            )
        )

        return (
            TorobResponseBuilder
            .build_paginated_response(
                variants=variants,
                page=page,
                total=total,
                request=request,
            )
        )

    @staticmethod
    def handle_page_uniques(
        *,
        request,
        validated_data,
    ) -> dict:
        """
        دریافت چند محصول بر اساس page_unique.
        """

        variants = (
            TorobProductSelector
            .get_by_page_uniques(
                validated_data["page_uniques"]
            )
        )

        return (
            TorobResponseBuilder
            .build_products_response(
                variants=variants,
                request=request,
            )
        )

    @staticmethod
    def handle_page_urls(
        *,
        request,
        validated_data,
    ) -> dict:
        """
        دریافت چند محصول بر اساس page_url.
        """

        variants = (
            TorobProductSelector
            .get_by_page_urls(
                validated_data["page_urls"]
            )
        )

        return (
            TorobResponseBuilder
            .build_products_response(
                variants=variants,
                request=request,
            )
        )

    @classmethod
    def build_initial_log_data(
        cls,
        request,
    ) -> dict:
        """
        داده‌های اولیه ثبت لاگ درخواست.

        توکن کامل JWT هرگز در دیتابیس ذخیره نمی‌شود.
        """

        request_body = request.data

        if not isinstance(request_body, dict):
            request_body = {}

        token_version = (
            request.headers.get(
                "X-Torob-Token-Version",
                "",
            )
            or request.headers.get(
                "C-Torob-Token-Version",
                "",
            )
        )

        return {
            "request_type": (
                TorobRequestLog.RequestType.INVALID
            ),
            "method": request.method,
            "endpoint": request.path[:500],
            "request_body": request_body,
            "response_status": 500,
            "products_count": 0,
            "total_products": 0,
            "requested_items_count": 0,
            "auth_status": cls.get_auth_status(
                request
            ),
            "token_version": token_version[:20],
            "ip_address": cls.get_client_ip(
                request
            ),
            "user_agent": request.headers.get(
                "User-Agent",
                "",
            ),
        }

    @staticmethod
    def get_auth_status(request) -> str:
        """
        تعیین وضعیت اعتبارسنجی JWT برای ثبت در لاگ.
        """

        auth_data = getattr(
            request,
            "auth",
            None,
        )

        if not isinstance(auth_data, dict):
            return (
                TorobRequestLog
                .AuthStatus
                .NOT_CHECKED
            )

        if auth_data.get("auth_status") == "valid":
            return (
                TorobRequestLog
                .AuthStatus
                .VALID
            )

        return (
            TorobRequestLog
            .AuthStatus
            .NOT_CHECKED
        )

    @staticmethod
    def get_client_ip(request) -> str | None:
        """
        دریافت IP درخواست‌کننده.

        اگر پروژه پشت reverse proxy باشد،
        اولین IP داخل X-Forwarded-For خوانده می‌شود.
        """

        forwarded_for = request.META.get(
            "HTTP_X_FORWARDED_FOR"
        )

        if forwarded_for:
            return forwarded_for.split(
                ","
            )[0].strip()

        return request.META.get(
            "REMOTE_ADDR"
        )

    @staticmethod
    def calculate_duration_ms(
        started_at: float,
    ) -> int:
        """
        محاسبه مدت پردازش درخواست بر حسب میلی‌ثانیه.
        """

        duration_seconds = (
            time.perf_counter() - started_at
        )

        return max(
            0,
            int(duration_seconds * 1000),
        )

    @classmethod
    def extract_error_message(
        cls,
        errors,
    ) -> str:
        """
        تبدیل خطاهای DRF به متن ساده مطابق فرمت ترب.

        خروجی نهایی:

            {
                "error": "error message"
            }
        """

        if isinstance(errors, dict):
            for field_name, value in errors.items():
                message = cls.extract_error_message(
                    value
                )

                if field_name == "non_field_errors":
                    return message

                return f"{field_name}: {message}"

        if isinstance(errors, (list, tuple)):
            if not errors:
                return "Invalid request."

            return cls.extract_error_message(
                errors[0]
            )

        return str(errors)

    @staticmethod
    def create_log_safely(
        log_data: dict,
    ) -> None:
        """
        خطای ثبت لاگ نباید پاسخ اصلی API را خراب کند.
        """

        try:
            TorobRequestLog.objects.create(
                **log_data
            )
        except Exception:
            pass
