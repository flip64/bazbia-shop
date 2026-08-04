from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponseRedirect

from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from payments.models import Payment
from payments.services.zarinpal_callback_service import (
    ZarinpalCallbackService,
)


class ZarinpalCallbackView(APIView):
    """
    دریافت نتیجه بازگشت کاربر از زرین‌پال.

    Example:
    GET /api/payments/callback/zarinpal/
        ?Authority=A000...
        &Status=OK
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    http_method_names = [
        "get",
        "head",
        "options",
    ]

    def get(
        self,
        request,
        *args,
        **kwargs,
    ):
        authority = str(
            request.query_params.get("Authority")
            or request.query_params.get("authority")
            or ""
        ).strip()

        callback_status = str(
            request.query_params.get("Status")
            or request.query_params.get("status")
            or ""
        ).strip().upper()

        if not authority:
            return self._redirect_to_frontend(
                result_status="failed",
                message=(
                    "شناسه Authority در پاسخ "
                    "زرین‌پال وجود ندارد."
                ),
            )

        payment = (
            Payment.objects
            .select_related("order")
            .filter(
                authority=authority,
                gateway="zarinpal",
            )
            .order_by("-id")
            .first()
        )

        if payment is None:
            return self._redirect_to_frontend(
                result_status="failed",
                authority=authority,
                message=(
                    "تراکنش مرتبط با این Authority "
                    "در سیستم پیدا نشد."
                ),
            )

        try:
            result = ZarinpalCallbackService(
                payment=payment,
                authority=authority,
                callback_status=callback_status,
            ).run()

        except ValueError as error:
            payment.refresh_from_db()

            return self._redirect_to_frontend(
                result_status="failed",
                payment=payment,
                authority=authority,
                message=str(error),
            )

        payment = result.payment

        if result.is_successful:
            result_status = "success"

        elif (
            payment.status
            == Payment.Status.CANCELLED
        ):
            result_status = "cancelled"

        else:
            result_status = "failed"

        return self._redirect_to_frontend(
            result_status=result_status,
            payment=payment,
            authority=authority,
            message=result.message,
        )

    @staticmethod
    def _redirect_to_frontend(
        *,
        result_status,
        payment=None,
        authority="",
        message="",
    ):
        frontend_url = str(
            getattr(
                settings,
                "PAYMENT_FRONTEND_RESULT_URL",
                "https://bazbia.ir/payment/verify",
            )
        ).strip()

        if not frontend_url:
            frontend_url = (
                "https://bazbia.ir/payment/verify"
            )

        query_params = {
            "payment_result": result_status,
        }

        if result_status == "success":
            query_params["mock_status"] = "success"

        elif result_status == "cancelled":
            query_params["mock_status"] = "cancelled"

        else:
            query_params["mock_status"] = "failed"

        if authority:
            query_params["authority"] = authority

        if payment is not None:
            query_params.update(
                {
                    "payment_id": str(payment.id),
                    "order_id": str(
                        payment.order_id
                    ),
                    "payment_status": (
                        payment.status
                    ),
                }
            )

        if message:
            query_params["message"] = message

        separator = (
            "&"
            if "?" in frontend_url
            else "?"
        )

        redirect_url = (
            f"{frontend_url}"
            f"{separator}"
            f"{urlencode(query_params)}"
        )

        return HttpResponseRedirect(
            redirect_url
        )
