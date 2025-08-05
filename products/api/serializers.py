from rest_framework import serializers
from products.models import Product  # یا اسم مدل خودت
from products.models import Category  # مدل دسته‌بندی شما


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'




class CategorySerializer(serializers.ModelSerializer):
    parent_id = serializers.IntegerField(source='parent.id', read_only=True)  # تبدیل parent به parent_id

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent_id', 'body']  # فیلدها رو طبق مدل و خروجی مورد نظر انتخاب کن
