from rest_framework import generics
from products.models import Product
from products.api.serializers import ProductSerializer
from products.api.pagination import CustomCategoryPagination
from products.models import Category , Product
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import CategorySerializer , ProductImageSerializer
from rest_framework import generics






class ProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset





class ProductDetailAPIView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    lookup_field = 'slug'




class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer







@api_view(['GET'])
def list_categories(request):
    categories = Category.objects.all()
    serializer = CategorySerializer(categories, many=True)
    return Response({
        "current_page": 1,
        "data": serializer.data
    })
