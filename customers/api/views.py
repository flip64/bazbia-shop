from django.contrib.auth.models import User
from django.db import transaction

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from customers.api.serializers import (
    LoginSerializer,
    RequestOTPSerializer,
    VerifyOTPSerializer,
)

from customers.models import Customer, OTP
from customers.services.otp_service import create_otp, verify_otp


class RequestOTPView(APIView):
    """
    درخواست ارسال کد ورود با شماره موبایل
    """

    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]

        otp, code = create_otp(
            phone=phone,
            purpose=OTP.Purpose.LOGIN,
        )

        # موقتاً تا زمان اتصال سرویس پیامک
        print(f"OTP for {phone}: {code}")

        response_data = {
            "message": "کد تأیید ارسال شد.",
            "session_id": str(otp.session_id),
            "expires_at": otp.expires_at,
        }

        # فقط برای محیط توسعه
        response_data["debug_code"] = code

        return Response(
            response_data,
            status=status.HTTP_200_OK,
        )


class VerifyOTPView(APIView):
    """
    بررسی کد ورود و صدور توکن JWT
    """

    @transaction.atomic
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session_id = serializer.validated_data["session_id"]
        code = serializer.validated_data["code"]

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
                status=status.HTTP_400_BAD_REQUEST,
            )

        phone = otp.phone

        user, user_created = User.objects.get_or_create(
            username=phone,
            defaults={
                "is_active": True,
            },
        )

        customer, customer_created = Customer.objects.get_or_create(
            user=user,
            defaults={
                "phone": phone,
            },
        )

        if not customer.phone:
            customer.phone = phone
            customer.save(update_fields=["phone"])

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "ورود با موفقیت انجام شد.",
                "is_new_user": user_created,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "phone": customer.phone,
                    "avatar": (
                        customer.avatar.url
                        if customer.avatar
                        else None
                    ),
                },
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    """
    ورود با شماره موبایل و رمز عبور
    """

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        try:
            customer = user.customer_profile
        except Customer.DoesNotExist:
            customer = None

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "ورود با موفقیت انجام شد.",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "phone": customer.phone if customer else None,
                    "avatar": (
                        customer.avatar.url
                        if customer and customer.avatar
                        else None
                    ),
                },
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_200_OK,
        )


class CurrentUserView(APIView):
    """
    دریافت اطلاعات کاربر واردشده
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        try:
            customer = user.customer_profile
        except Customer.DoesNotExist:
            customer = None

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone": customer.phone if customer else None,
                "avatar": (
                    customer.avatar.url
                    if customer and customer.avatar
                    else None
                ),
            },
            status=status.HTTP_200_OK,
        )