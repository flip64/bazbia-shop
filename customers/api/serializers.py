from rest_framework import serializers
from django.contrib.auth.models import User
from customers.models import Customer,OTP
from django.contrib.auth import authenticate



class RegisterSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "phone"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        phone = validated_data.pop("phone","")

        # ساخت یوزر
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email"),
            password=validated_data["password"]
        )

        # ساخت پروفایل Customer
        Customer.objects.create(
            user=user,
            phone=phone,
        )

        return user


# customers/serializers.py

class SendOtpSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)

class VerifyOtpSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=4)



class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get("username")
        print(username)
        password = data.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError("اکانت شما غیرفعال است.")
                data["user"] = user
            else:
                raise serializers.ValidationError("یوزرنیم یا پسورد اشتباه است.")
        else:
            raise serializers.ValidationError("یوزرنیم و پسورد الزامی است.")

        return data
