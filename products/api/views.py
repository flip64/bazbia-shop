from rest_framework import generics
from products.models import Product
from products.api.serializers import ProductSerializer
from products.api.pagination import CustomCategoryPagination
from products.models import Category
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import CategorySerializer



class ProductListAPIView(generics.ListAPIView):
    queryset = Product.objects.all()
    print(queryset)
    serializer_class = ProductSerializer
    pagination_class = CustomCategoryPagination



@api_view(['GET'])
def list_categories(request):
    categories = Category.objects.all()
    serializer = CategorySerializer(categories, many=True)
    return Response({
        "current_page": 1,
        "data": serializer.data
    })
