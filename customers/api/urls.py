from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from customers.api.views import (
    CustomerAddressViewSet,
    CurrentUserView,
    LoginView,
    LogoutView,
    RequestOTPView,
    VerifyOTPView,
)


app_name = "customers"


router = DefaultRouter()

router.register(
    r"addresses",
    CustomerAddressViewSet,
    basename="customer-address",
)


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
        "auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token-refresh",
    ),
    path(
        "auth/logout/",
        LogoutView.as_view(),
        name="logout",
    ),
    path(
        "auth/me/",
        CurrentUserView.as_view(),
        name="current-user",
    ),

    # مسیرهای مدیریت آدرس‌های مشتری
    path(
        "",
        include(router.urls),
    ),
]
