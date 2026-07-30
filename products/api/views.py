from django.db import transaction
from django.db.models import (
    Exists,
    F,
    Min,
    OuterRef,
)
from django.http import (
    HttpResponseBadRequest,
    JsonResponse,
)
from django.views.decorators.csrf import (
    csrf_exempt,
)

from rest_framework import (
    generics,
    status,
)
from rest_framework.decorators import api_view
from rest_framework.response import Response

import json

from products.models import (
    Category,
    Product,
    ProductVariant,
    SpecialProduct,
)
from products.api.pagination import (
    CustomCategoryPagination,
)
from products.api.serializers import (
    CategorySerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    ProductSerializer,
    SpecialProductSerializer,
)


# =============================
# Product filter mixin
# =============================

class ProductFilterMixin:
    """
    فیلتر و مرتب‌سازی مشترک محصولات.

    ترتیب نهایی همیشه به این صورت است:

    1. تمام محصولات موجود
    2. تمام محصولات ناموجود

    داخل هر گروه، مرتب‌سازی انتخاب‌شده کاربر
    مانند جدیدترین، قدیمی‌ترین یا قیمت اعمال می‌شود.
    """

    def apply_filters(self, queryset):
        available_variant_queryset = (
            ProductVariant.objects.filter(
                product_id=OuterRef("pk"),
                stock__gt=0,
            )
        )

        discounted_variant_queryset = (
            ProductVariant.objects.filter(
                product_id=OuterRef("pk"),
                discount_price__isnull=False,
                discount_price__gt=0,
                discount_price__lt=F("price"),
            )
        )

        queryset = queryset.annotate(
            min_price=Min(
                "variants__price",
            ),
            has_available_variant=Exists(
                available_variant_queryset,
            ),
            has_discount_variant=Exists(
                discounted_variant_queryset,
            ),
        )

        # دسته‌بندی
        category = (
            self.request.query_params.get(
                "category",
            )
        )

        if category:
            queryset = queryset.filter(
                category__slug=category,
            )

        # تگ
        tag = self.request.query_params.get(
            "tag",
        )

        if tag:
            queryset = queryset.filter(
                tags__slug=tag,
            )

        # جستجو
        search = (
            self.request.query_params.get(
                "search",
            )
        )

        if search:
            queryset = queryset.filter(
                name__icontains=search,
            )

        # حداقل قیمت
        min_price = (
            self.request.query_params.get(
                "min_price",
            )
        )

        if min_price:
            queryset = queryset.filter(
                min_price__gte=min_price,
            )

        # حداکثر قیمت
        max_price = (
            self.request.query_params.get(
                "max_price",
            )
        )

        if max_price:
            queryset = queryset.filter(
                min_price__lte=max_price,
            )

        # فقط محصولات موجود
        in_stock = (
            self.request.query_params.get(
                "in_stock",
            )
        )

        if in_stock == "true":
            queryset = queryset.filter(
                has_available_variant=True,
            )

        # فقط محصولات تخفیف‌دار
        has_discount = (
            self.request.query_params.get(
                "has_discount",
            )
        )

        if has_discount == "true":
            queryset = queryset.filter(
                has_discount_variant=True,
            )

        # محصولات ویژه
        special = (
            self.request.query_params.get(
                "special",
            )
        )

        if special == "true":
            queryset = queryset.filter(
                special__is_active=True,
            )

        # مرتب‌سازی انتخاب‌شده کاربر
        ordering = (
            self.request.query_params.get(
                "ordering",
            )
        )

        ordering_map = {
            "-created_at": (
                "-created_at",
                "-id",
            ),
            "created_at": (
                "created_at",
                "id",
            ),
            "price": (
                "min_price",
                "id",
            ),
            "-price": (
                "-min_price",
                "-id",
            ),
        }

        selected_ordering = (
            ordering_map.get(
                ordering,
                (
                    "-id",
                ),
            )
        )

        # اول موجودها، سپس ناموجودها
        queryset = queryset.order_by(
            "-has_available_variant",
            *selected_ordering,
        )

        return queryset.distinct()


# =============================
# Product List
# با صفحه‌بندی و فیلترها
# =============================

class ProductListAPIView(
    ProductFilterMixin,
    generics.ListAPIView,
):
    serializer_class = ProductListSerializer
    pagination_class = (
        CustomCategoryPagination
    )

    def get_queryset(self):
        queryset = (
            Product.objects.filter(
                is_active=True,
                variants__isnull=False,
            )
            .prefetch_related(
                "variants",
                "images",
                "tags",
            )
        )

        return self.apply_filters(
            queryset,
        )


# =============================
# Product Full List
# تمام جزئیات
# =============================

class ProductFullListAPIView(
    ProductFilterMixin,
    generics.ListAPIView,
):
    serializer_class = (
        ProductDetailSerializer
    )
    pagination_class = (
        CustomCategoryPagination
    )

    def get_queryset(self):
        queryset = (
            Product.objects.filter(
                is_active=True,
                variants__isnull=False,
            )
            .prefetch_related(
                "variants",
                "variants__attributes",
                "images",
                "videos",
                "tags",
                "specifications",
            )
        )

        return self.apply_filters(
            queryset,
        )


# =============================
# Product Detail
# =============================

class ProductDetailAPIView(
    generics.RetrieveAPIView,
):
    queryset = Product.objects.filter(
        is_active=True,
    )
    serializer_class = (
        ProductDetailSerializer
    )
    lookup_field = "slug"

    def retrieve(
        self,
        request,
        *args,
        **kwargs,
    ):
        try:
            instance = self.get_object()

            serializer = (
                self.get_serializer(
                    instance,
                )
            )

            return Response(
                serializer.data,
            )

        except Product.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "محصول یافت نشد"
                    ),
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )


# =============================
# Category List
# =============================

class CategoryListAPIView(
    generics.ListAPIView,
):
    queryset = Category.objects.filter(
        parent__isnull=True,
    )
    serializer_class = CategorySerializer


# =============================
# Products by Category
# شامل زیرشاخه‌ها
# =============================

class ProductListCategoryAPIView(
    ProductFilterMixin,
    generics.ListAPIView,
):
    serializer_class = ProductListSerializer
    pagination_class = (
        CustomCategoryPagination
    )

    def get_category_and_descendants_ids(
        self,
        category,
    ):
        category_ids = [
            category.id,
        ]

        for child in (
            category.subcategories.all()
        ):
            category_ids.extend(
                self
                .get_category_and_descendants_ids(
                    child,
                ),
            )

        return category_ids

    def get_queryset(self):
        category_slug = (
            self.kwargs.get(
                "slug",
            )
        )

        queryset = (
            Product.objects.filter(
                is_active=True,
                variants__isnull=False,
            )
            .prefetch_related(
                "variants",
                "images",
                "tags",
            )
        )

        if category_slug:
            try:
                category = (
                    Category.objects.get(
                        slug=category_slug,
                    )
                )

                category_ids = (
                    self
                    .get_category_and_descendants_ids(
                        category,
                    )
                )

                queryset = queryset.filter(
                    category_id__in=(
                        category_ids
                    ),
                )

            except Category.DoesNotExist:
                return (
                    Product.objects.none()
                )

        return self.apply_filters(
            queryset,
        )

    def list(
        self,
        request,
        *args,
        **kwargs,
    ):
        category_slug = (
            self.kwargs.get(
                "slug",
            )
        )

        subcategories = []

        if category_slug:
            try:
                category = (
                    Category.objects.get(
                        slug=category_slug,
                    )
                )

                subcategories_queryset = (
                    category
                    .subcategories
                    .all()
                )

                subcategories = [
                    {
                        "id": item.id,
                        "name": item.name,
                        "slug": item.slug,
                        "image": (
                            request
                            .build_absolute_uri(
                                item.image.url,
                            )
                            if item.image
                            else None
                        ),
                    }
                    for item in (
                        subcategories_queryset
                    )
                ]

            except Category.DoesNotExist:
                pass

        queryset = self.get_queryset()

        page = self.paginate_queryset(
            queryset,
        )

        if page is not None:
            serializer = self.get_serializer(
                page,
                many=True,
                context={
                    "request": request,
                },
            )

            paginated_response = (
                self
                .get_paginated_response(
                    serializer.data,
                )
            )

            response_data = (
                paginated_response.data
            )

        else:
            serializer = self.get_serializer(
                queryset,
                many=True,
                context={
                    "request": request,
                },
            )

            response_data = {
                "count": queryset.count(),
                "data": serializer.data,
            }

        response_data["success"] = True

        response_data[
            "subcategories"
        ] = subcategories

        return Response(
            response_data,
        )


# =============================
# Categories as Tree
# =============================

@api_view(["GET"])
def list_categories(request):
    def build_tree(parent=None):
        categories = (
            Category.objects.filter(
                parent=parent,
            )
            .values(
                "id",
                "name",
                "slug",
            )
        )

        tree = []

        for category in categories:
            children = build_tree(
                parent=category["id"],
            )

            item = {
                "id": category["id"],
                "name": category["name"],
                "slug": category["slug"],
            }

            if children:
                item["children"] = children

            tree.append(item)

        return tree

    data = build_tree()

    return JsonResponse(
        data,
        safe=False,
    )


# =============================
# List Children of a Category
# =============================

@api_view(["GET"])
def category_children(
    request,
    slug,
):
    try:
        parent = Category.objects.get(
            slug=slug,
        )

    except Category.DoesNotExist:
        return Response(
            {
                "error": (
                    "دسته‌بندی یافت نشد"
                ),
            },
            status=404,
        )

    children = (
        parent
        .subcategories
        .all()
        .values(
            "id",
            "name",
            "slug",
        )
    )

    return Response(
        list(children),
    )


# =============================
# Import Categories from JSON
# =============================

@csrf_exempt
def import_categories(request):
    if request.method != "POST":
        return HttpResponseBadRequest(
            "Only POST method allowed",
        )

    try:
        payload = json.loads(
            request.body,
        )

    except json.JSONDecodeError:
        return HttpResponseBadRequest(
            "Invalid JSON",
        )

    created = []

    @transaction.atomic
    def create_or_get_category(
        item,
        parent=None,
    ):
        slug = item["slug"]
        name = item["name"]

        category, is_created = (
            Category.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "parent": parent,
                },
            )
        )

        if is_created:
            created.append(
                category.name,
            )

        for child in item.get(
            "children",
            [],
        ):
            create_or_get_category(
                child,
                parent=category,
            )

    for category_item in payload:
        create_or_get_category(
            category_item,
        )

    return JsonResponse(
        {
            "status": "done",
            "created": created,
        },
    )
