from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import json

from products.models import Product, Category, SpecialProduct
from products.api.serializers import (
    ProductSerializer,
    ProductDetailSerializer,
    SpecialProductSerializer,
    CategorySerializer,
    ProductListSerializer
)
from products.api.pagination import CustomCategoryPagination


# -----------------------------
# List All Products
# -----------------------------
class ProductListAPIView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    pagination_class = CustomCategoryPagination  # اضافه شد

    def get_queryset(self):
     
     category_slug = self.kwargs.get("slug")
     queryset = Product.objects.filter(
         is_active=True,
         variants__isnull=False  # حداقل یک واریانت
            ).order_by("-id").distinct()

     if category_slug:
         queryset = queryset.filter(category__slug=category_slug)

        
     return queryset


# -----------------------------
# Product Detail
# -----------------------------
class ProductDetailAPIView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductDetailSerializer
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


# -----------------------------
# List All Categories
# -----------------------------
class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


# -----------------------------
# List Special Products
# -----------------------------
class SpecialProductListAPIView(generics.ListAPIView):
    serializer_class = SpecialProductSerializer

    def get_queryset(self):
        return SpecialProduct.objects.filter(is_active=True)


# -----------------------------
# List New Products
# -----------------------------
class NewProductsAPIView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).order_by('-created_at')
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset[:30]



# -----------------------------

# List Products By Category
# -----------------------------
class ProductListCategoryAPIView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    pagination_class = CustomCategoryPagination

    def get_queryset(self):
        category_slug = self.kwargs.get("slug")
        queryset = Product.objects.filter(is_active=True)
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


# -----------------------------
# List Categories as Tree
# -----------------------------
@api_view(['GET'])
def list_categories(request):
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


# -----------------------------
# Import Categories from JSON
# -----------------------------
@csrf_exempt
def import_categories(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST method allowed")

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    created = []

    @transaction.atomic
    def create_or_get_category(item, parent=None):
        slug = item['slug']
        name = item['name']

        category, is_created = Category.objects.get_or_create(
            slug=slug,
            defaults={'name': name, 'parent': parent}
        )

        if is_created:
            created.append(category.name)

        for child in item.get('children', []):
            create_or_get_category(child, parent=category)

    for cat_item in payload:
        create_or_get_category(cat_item)

    return JsonResponse({"status": "done", "created": created})
