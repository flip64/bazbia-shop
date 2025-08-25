from rest_framework            import  generics
from products.models           import  Product
from products.api.serializers  import  ProductSerializer,SpecialProductSerializer
from products.api.pagination   import  CustomCategoryPagination
from products.models           import  Category , Product , SpecialProduct
from rest_framework.decorators import  api_view
from rest_framework.response   import  Response
from products.api.serializers  import  CategorySerializer , ProductImageSerializer
from products.api.serializers  import  NewProductSerializer
from products.api.serializers  import  ProductDetailSerializer
from rest_framework.views      import  APIView






class ProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)[:30]
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



class SpecialProductListAPIView(generics.ListAPIView):
    serializer_class = SpecialProductSerializer
    def get_queryset(self):
        return SpecialProduct.objects.filter(is_active=True)



class NewProductsAPIView(APIView):
    def get(self, request):
       new_products = Product.objects.order_by('-created_at')[:30]
       serializer = NewProductSerializer(new_products, many=True, context={'request': request})
       return Response(serializer.data)




class ProductDetailAPIView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductDetailSerializer
    lookup_field = 'slug'
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Product.DoesNotExist:
            return Response({
                'success': False,
                'message': 'محصول یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)



@api_view(['GET'])
def list_categories(request):
    categories = Category.objects.all()
    serializer = CategorySerializer(categories, many=True)
    return Response({
        "current_page": 1,
        "data": serializer.data
    })

