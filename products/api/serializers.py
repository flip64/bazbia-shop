from rest_framework import serializers
from products.models import Product  # یا اسم مدل خودت

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
