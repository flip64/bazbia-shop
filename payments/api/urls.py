from django.urls import path

from payments.api.views import (
    CreatePaymentView,
)


app_name = "payments"


urlpatterns = [
    path(
        "create/",
        CreatePaymentView.as_view(),
        name="payment-create",
    ),
]
