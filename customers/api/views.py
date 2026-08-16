from django.contrib.auth.models import User
from django.db import transaction

from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from customers.models import (
    Customer,
    CustomerAddress,
    OTP,
)

from customers.api.serializers import (
    CustomerAddressSerializer,
    LoginSerializer,
    LogoutSerializer,
    RequestOTPSerializer,
    VerifyOTPSerializer,
)

from customers.services.otp_service import (
    create_otp,
    verify_otp,
)


# =========================================================
# User data helper
# =========================================================

def build_user_data(user):
    """
    ساخت پاسخ استاندارد اطلاعات کاربر.

    این تابع در ورود با رمز عبور، ورود با OTP
    و دریافت اطلاعات کاربر استفاده می‌شود.
    """

    try:
        customer = user.customer_profile
    except Customer.DoesNotExist:
        customer = None

    first_name = user.first_name or ""
    last_name = user.last_name or ""

    full_name = (
        f"{first_name} {last_name}"
        .strip()
    )

    avatar_url = None

    if (
        customer
        and customer.avatar
    ):
        try:
            avatar_url = customer.avatar.url
        except ValueError:
            avatar_url = None

    return {
        "id": user.id,
        "username": user.username,

        "first_name": first_name,
        "last_name": last_name,
        "full_name": full_name,

        "email": user.email or "",

        "phone": (
            customer.phone
            if customer
            else None
        ),

        "avatar": avatar_url,
    }


# =========================================================
# Request OTP
# =========================================================

class RequestOTPView(APIView):
    """
    درخواست ارسال کد ورود با شماره موبایل.
    """

    permission_classes = [
        permissions.AllowAny,
    ]

    def post(self, request):
        serializer = RequestOTPSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        phone = serializer.validated_data[
            "phone"
        ]

        try:
            otp, _ = create_otp(
                phone=phone,
                purpose=OTP.Purpose.LOGIN,
            )

        except ValueError as error:
            return Response(
                {
                    "error": str(error),
                },
                status=(
                    status
                    .HTTP_429_TOO_MANY_REQUESTS
                ),
            )

        return Response(
            {
                "message": (
                    "کد تأیید ارسال شد."
                ),
                "session_id": str(
                    otp.session_id
                ),
                "expires_at": (
                    otp.expires_at
                ),
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# Verify OTP
# =========================================================

class VerifyOTPView(APIView):
    """
    بررسی کد ورود و صدور توکن JWT.
    """

    permission_classes = [
        permissions.AllowAny,
    ]

    @transaction.atomic
    def post(self, request):
        serializer = VerifyOTPSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        session_id = serializer.validated_data[
            "session_id"
        ]

        code = serializer.validated_data[
            "code"
        ]

        try:
            otp = verify_otp(
                session_id=session_id,
                code=code,
            )

        except ValueError as error:
            return Response(
                {
                    "error": str(error),
                },
                status=(
                    status
                    .HTTP_400_BAD_REQUEST
                ),
            )

        phone = otp.phone

        # ---------------------------------
        # User
        # ---------------------------------

        user, user_created = (
            User.objects.get_or_create(
                username=phone,
                defaults={
                    "is_active": True,
                },
            )
        )

        if not user.is_active:
            return Response(
                {
                    "error": (
                        "حساب کاربری غیرفعال است."
                    ),
                },
                status=(
                    status
                    .HTTP_403_FORBIDDEN
                ),
            )

        # ---------------------------------
        # Customer
        # ---------------------------------

        customer, _ = (
            Customer.objects.get_or_create(
                user=user,
                defaults={
                    "phone": phone,
                },
            )
        )

        if not customer.phone:
            customer.phone = phone

            customer.save(
                update_fields=[
                    "phone",
                ]
            )

        # ---------------------------------
        # JWT
        # ---------------------------------

        refresh = RefreshToken.for_user(
            user
        )

        # ---------------------------------
        # Response
        # ---------------------------------

        return Response(
            {
                "message": (
                    "ورود با موفقیت انجام شد."
                ),

                "is_new_user": user_created,

                "user": build_user_data(
                    user
                ),

                "tokens": {
                    "refresh": str(
                        refresh
                    ),
                    "access": str(
                        refresh.access_token
                    ),
                },
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# Login
# =========================================================

class LoginView(APIView):
    """
    ورود با شماره موبایل و رمز عبور.
    """

    permission_classes = [
        permissions.AllowAny,
    ]

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        user = serializer.validated_data[
            "user"
        ]

        if not user.is_active:
            return Response(
                {
                    "error": (
                        "حساب کاربری غیرفعال است."
                    ),
                },
                status=(
                    status
                    .HTTP_403_FORBIDDEN
                ),
            )

        refresh = RefreshToken.for_user(
            user
        )

        return Response(
            {
                "message": (
                    "ورود با موفقیت انجام شد."
                ),

                "user": build_user_data(
                    user
                ),

                "tokens": {
                    "refresh": str(
                        refresh
                    ),
                    "access": str(
                        refresh.access_token
                    ),
                },
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# Current User
# =========================================================

class CurrentUserView(APIView):
    """
    دریافت اطلاعات کاربر واردشده.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        return Response(
            build_user_data(
                request.user
            ),
            status=status.HTTP_200_OK,
        )


# =========================================================
# Logout
# =========================================================

class LogoutView(APIView):
    """
    خروج کاربر و باطل‌کردن Refresh Token.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        serializer = LogoutSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        refresh_token = serializer.validated_data[
            "refresh"
        ]

        try:
            token = RefreshToken(
                refresh_token
            )

            token_user_id = str(
                token["user_id"]
            )

            current_user_id = str(
                request.user.id
            )

            if token_user_id != current_user_id:
                return Response(
                    {
                        "error": (
                            "این توکن متعلق به "
                            "کاربر فعلی نیست."
                        ),
                    },
                    status=(
                        status
                        .HTTP_403_FORBIDDEN
                    ),
                )

            token.blacklist()

        except TokenError:
            return Response(
                {
                    "error": (
                        "توکن تمدید نامعتبر "
                        "یا قبلاً باطل شده است."
                    ),
                },
                status=(
                    status
                    .HTTP_400_BAD_REQUEST
                ),
            )

        return Response(
            {
                "message": (
                    "خروج با موفقیت انجام شد."
                ),
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# Customer Address
# =========================================================

class CustomerAddressViewSet(
    viewsets.ModelViewSet
):
    """
    مدیریت آدرس‌های مشتری واردشده.

    هر کاربر فقط آدرس‌های متعلق به پروفایل
    مشتری خودش را مشاهده، ثبت، ویرایش
    و حذف می‌کند.
    """

    serializer_class = (
        CustomerAddressSerializer
    )

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_queryset(self):
        customer = getattr(
            self.request.user,
            "customer_profile",
            None,
        )

        if customer is None:
            return (
                CustomerAddress
                .objects
                .none()
            )

        return (
            CustomerAddress.objects
            .filter(
                customer=customer
            )
            .order_by(
                "-is_default",
                "-updated_at",
            )
        )

    def perform_create(
        self,
        serializer,
    ):
        customer = getattr(
            self.request.user,
            "customer_profile",
            None,
        )

        if customer is None:
            raise ValidationError(
                {
                    "detail": (
                        "برای این کاربر پروفایل "
                        "مشتری ایجاد نشده است."
                    )
                }
            )

        serializer.save(
            customer=customer
        )
