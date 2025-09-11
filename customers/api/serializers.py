from rest_framework import serializers
from django.contrib.auth.models import User
from customers.models import Customer



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
