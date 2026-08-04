from django.urls import path

from payments.api.views import (
    CreatePaymentView,
    PaymentDetailView,
    VerifyPaymentView,
    ZarinpalCallbackView,
)


app_name = "payments"


urlpatterns = [
    path(
        "create/",
        CreatePaymentView.as_view(),
        name="payment-create",
    ),

    path(
        "verify/",
        VerifyPaymentView.as_view(),
        name="payment-verify",
    ),

    path(
        "callback/zarinpal/",
        ZarinpalCallbackView.as_view(),
        name="zarinpal-callback",
    ),

    path(
        "<int:payment_id>/",
        PaymentDetailView.as_view(),
        name="payment-detail",
    ),
]
