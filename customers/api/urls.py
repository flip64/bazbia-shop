from django.urls import path

from customers.api.views import (
    CurrentUserView,
    LoginView,
    RequestOTPView,
    VerifyOTPView,
)


app_name = "customers"


urlpatterns = [
    path(
        "auth/login/password/",
        LoginView.as_view(),
        name="password-login",
    ),
    path(
        "auth/otp/request/",
        RequestOTPView.as_view(),
        name="otp-request",
    ),
    path(
        "auth/otp/verify/",
        VerifyOTPView.as_view(),
        name="otp-verify",
    ),
    path(
        "auth/me/",
        CurrentUserView.as_view(),
        name="current-user",
    ),
]