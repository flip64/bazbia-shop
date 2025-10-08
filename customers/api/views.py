from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response

from django.contrib.auth.models import User
from customers.api.serializers import RegisterSerializer
from customers.models import CustomerState, Status
from customers.models import OTP ,Customer
from customers.api.serializers import SendOtpSerializer, VerifyOtpSerializer
from customers.api.serializers import LoginSerializer
import random



class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        print(serializer)

        if serializer.is_valid():
            user = serializer.save()
           
            # دریافت پروفایل مشتری
            customer = user.customer_profile

            # گرفتن یا ایجاد وضعیت پیش‌فرض شماره تلفن تأیید نشده
            status_phone_not_verified, created = Status.objects.get_or_create(
                code='phone_not_verified',
                defaults={'title': 'شماره تلفن تأیید نشده'}
            )

            # ایجاد CustomerState و افزودن وضعیت
            customer_state = CustomerState.objects.create(customer=customer)
            customer_state.statuses.add(status_phone_not_verified)

            # برگرداندن اطلاعات و توکن
            return Response(
                {
                    "message": "ثبت‌نام با موفقیت انجام شد",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "phone": customer.phone,
                        "statuses": [s.code for s in customer_state.statuses.all()]
                    },
                   
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# customers/views.py

class SendOtpView(APIView):
    def post(self, request):
        serializer = SendOtpSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            # ساختن OTP تصادفی  4 رقمی
            code = str(random.randint(1000, 9999))
            otp = OTP.objects.create(phone=phone, code=code)

            # TODO: در حالت واقعی باید کد رو با SMS بفرستی
            print(f"OTP for {phone}: {code}")

            return Response({
                "code":str(code),
                "message": "کد تایید ارسال شد",
                "session_id": str(otp.session_id)  # برای امنیت می‌تونی session_id برگردونی
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOtpView(APIView):
    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            code = serializer.validated_data['code']

            try:
                otp = OTP.objects.filter(phone=phone, code=code).latest('created_at')
            except OTP.DoesNotExist:
                return Response({"error": "کد معتبر نیست"}, status=status.HTTP_400_BAD_REQUEST)

            # بررسی اعتبار کد (مثلاً ۵ دقیقه)
            from django.utils import timezone
            from datetime import timedelta
            if otp.created_at < timezone.now() - timedelta(minutes=5):
                return Response({"error": "کد منقضی شده"}, status=status.HTTP_400_BAD_REQUEST)

            # پیدا کردن یا ساخت کاربر
            user, created = User.objects.get_or_create(
                username=phone,  # یوزرنیم = شماره موبایل
                defaults={"is_active": True}
            )

            # ساختن توکن‌ها
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token

            return Response(
                {
                    "message": "کد تایید شد ✅",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                    },
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(access),
                    },
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        try:
            customer = Customer.objects.get(user=user)
            avatar = customer.avatar.url if customer.avatar else None
        except Customer.DoesNotExist:
            customer = None
            avatar = None

        
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "avatar": avatar
        })



class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "ورود موفقیت‌آمیز بود.",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                },
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)
         
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
