from rest_framework import serializers
from django.contrib.auth.models import User
from customers.models import Customer



class RegisterSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(write_only=True)
    address = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["username", "email", "password", "phone", "address"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        phone = validated_data.pop("phone","")
        address = validated_data.pop("address", "")

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
            address=address
        )

        return user
