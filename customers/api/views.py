from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from customers.api.serializers import RegisterSerializer
from customers.models import CustomerState, Status

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # ساخت توکن JWT
            refresh = RefreshToken.for_user(user)

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
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    }
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
