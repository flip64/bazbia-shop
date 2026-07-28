from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Min
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

# =============================
# Product filter mixin 
# =============================

class ProductFilterMixin:

    def apply_filters(self, queryset):

        queryset = queryset.annotate(
           min_price=Min("variants__price")   
         ) 
        

        # دسته بندی
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(
                category__slug=category
            )



        # تگ
        tag = self.request.query_params.get("tag")
        if tag:
            queryset = queryset.filter(
                tags__slug=tag
            )



        # جستجو
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                name__icontains=search
            )

        # حداقل قیمت
        min_price = self.request.query_params.get("min_price")
        if min_price:
            queryset = queryset.filter(
                variants__price__gte=min_price
            )

        # حداکثر قیمت
        max_price = self.request.query_params.get("max_price")
        if max_price:
            queryset = queryset.filter(
                variants__price__lte=max_price
            )

        # موجودی
        in_stock = self.request.query_params.get("in_stock")
        if in_stock == "true":
            queryset = queryset.filter(
                variants__stock__gt=0
            )

        # محصولات ویژه
        special = self.request.query_params.get("special")
        if special == "true":
            queryset = queryset.filter(
                special__is_active=True
            )

        # مرتب سازی
        ordering = self.request.query_params.get("ordering")

        if ordering == "newest":
            queryset = queryset.order_by("-created_at")

        elif ordering == "oldest":
            queryset = queryset.order_by("created_at")

        elif ordering == "price_asc":
            queryset = queryset.order_by("min_price")

        elif ordering == "price_desc":
            queryset = queryset.order_by("-min_price")

        else:
            queryset = queryset.order_by("-id")

        return queryset.distinct()



# =============================
# Product List (با صفحه‌بندی و فیلتر دسته)
# =============================
class ProductListAPIView(
    ProductFilterMixin,
    generics.ListAPIView
):
    serializer_class = ProductListSerializer
    pagination_class = CustomCategoryPagination

    def get_queryset(self):
        queryset = Product.objects.filter(
            is_active=True,
            variants__isnull=False
        ).prefetch_related(
            "variants",
            "images",
            "tags"
        )

        return self.apply_filters(queryset)

# =============================
# Product Full List (تمام جزئیات)
# =============================

class ProductFullListAPIView(
    ProductFilterMixin,
    generics.ListAPIView
):
    serializer_class = ProductDetailSerializer
    pagination_class = CustomCategoryPagination

    def get_queryset(self):
        queryset = Product.objects.filter(
            is_active=True,
            variants__isnull=False
        ).prefetch_related(
            "variants",
            "variants__attributes",
            "images",
            "videos",
            "tags",
            "specifications"
        )

        return self.apply_filters(queryset)






# =============================
# Product Detail
# =============================
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


# =============================
# Category List
# =============================
class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.filter(parent__isnull=True)
    serializer_class = CategorySerializer



# =============================
# Products by Category (شامل زیرشاخه‌ها)
# =============================
class ProductListCategoryAPIView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    pagination_class = CustomCategoryPagination

    def get_category_and_descendants_ids(self, category):
        ids = [category.id]
        for child in category.subcategories.all():
            ids.extend(self.get_category_and_descendants_ids(child))
        return ids

    def get_queryset(self):
        category_slug = self.kwargs.get("slug")
        queryset = Product.objects.filter(is_active=True)

        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug)
                category_ids = self.get_category_and_descendants_ids(category)
                queryset = queryset.filter(category_id__in=category_ids)
            except Category.DoesNotExist:
                queryset = Product.objects.none()

        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        category_slug = self.kwargs.get("slug")
        subcategories = []

        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug)
                subcats = category.subcategories.all()
                subcategories = [
                    {
                        "id": c.id,
                        "name": c.name,
                        "slug": c.slug,
                        "image": request.build_absolute_uri(c.image.url) if c.image else None
                    }
                    for c in subcats
                ]
            except Category.DoesNotExist:
                pass

        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            paginated_response = self.get_paginated_response(serializer.data)
            response_data = paginated_response.data
        else:
            serializer = self.get_serializer(queryset, many=True, context={'request': request})
            response_data = {"count": queryset.count(), "data": serializer.data}

        response_data["success"] = True
        response_data["subcategories"] = subcategories
        return Response(response_data)


# =============================
# Categories as Tree
# =============================
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


# =============================
# List Children of a Category
# =============================
@api_view(['GET'])
def category_children(request, slug):
    try:
        parent = Category.objects.get(slug=slug)
    except Category.DoesNotExist:
        return Response({"error": "دسته‌بندی یافت نشد"}, status=404)

    children = parent.subcategories.all().values('id', 'name', 'slug')
    return Response(list(children))


# =============================
# Import Categories from JSON
# =============================
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



