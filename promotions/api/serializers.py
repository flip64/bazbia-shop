# promotions/serializers.py
from rest_framework import serializers
from promotions.models import Banner

class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ["id", "title", "image", "link", "created_at"]
