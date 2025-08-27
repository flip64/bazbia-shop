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
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
import json






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
    serializer_class = ProductDetailSerializer   # 🔹 این لازمه
    lookup_field = "slug"
  
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



class ProductListCategoryAPIView(generics.ListAPIView):
    print('of')
    serializer_class = ProductSerializer
    pagination_class = CustomCategoryPagination   # 🔹 اضافه شد

    def get_queryset(self):
        category_slug = self.kwargs.get("slug")  # گرفتن slug از URL
        queryset = Product.objects.filter(is_active=True)
        print(queryset)
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response({
            "success": True,
            "count": queryset.count(),
            "data": serializer.data
        })


@api_view(['GET'])
def list_categories(request):
    print('op')
    def build_tree(parent=None):
        categories = Category.objects.filter(parent=parent).values('id', 'name', 'slug')
        tree = []
        for cat in categories:
            children = build_tree(parent=cat['id'])
            item = {
                'id': cat['id'],
                'name': cat['name'],
                'slug': cat['slug'],
            }
            if children:
                item['children'] = children
            tree.append(item)
        return tree

    data = build_tree()
    return JsonResponse(data, safe=False)


@csrf_exempt
def import_categories(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST method allowed")

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    created = []

    def create_or_get_category(item, parent=None):
        slug = item['slug']
        name = item['name']

        category, is_created = Category.objects.get_or_create(
            slug=slug,
            defaults={'name': name, 'parent': parent}
        )

        # فقط اگر تازه ساخته شده اضافه کن به لیست
        if is_created:
            created.append(category.name)

        # بررسی children
        for child in item.get('children', []):
            create_or_get_category(child, parent=category)

    for cat_item in payload:
        create_or_get_category(cat_item)

    return JsonResponse({"status": "done","created": created})
