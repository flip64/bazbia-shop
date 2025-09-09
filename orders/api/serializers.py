# orders/api/serializers.py
from rest_framework import serializers
from products.models import Product

class ProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(read_only=True)
    thumb = serializers.ImageField(source='thumb', read_only=True)
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'base_price', 'category', 'thumb', 'created_at']

    def get_created_at(self, obj):
        # تبدیل تاریخ به رشته ISO بدون ارور tzinfo
        return obj.created_at.isoformat()
