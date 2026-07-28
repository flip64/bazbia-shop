from django.urls import path

from payments.api.views import (
    CreatePaymentView,
    VerifyPaymentView,
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
]
