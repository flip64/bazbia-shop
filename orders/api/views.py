# orders/api/views.py

from datetime import timedelta

from django.db import transaction
from django.db.models import (
    Case,
    IntegerField,
    Sum,
    When,
)
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from products.models import (
    Product,
    ProductVariant,
)
from products.api.pagination import CustomCategoryPagination
from products.api.serializers import ProductListSerializer

from orders.models import (
    Cart,
    CartItem,
    Order,
    OrderItem,
    SalesSummary,
)
from orders.api.serializers import (
    CartItemCreateSerializer,
    CartItemSerializer,
    CartItemUpdateSerializer,
    CartSerializer,
    OrderSerializer,
)


# حداکثر تعداد مجاز از هر واریانت در سبد
MAX_CART_ITEM_QUANTITY = 10


# =========================================================
# توابع کمکی سبد خرید
# =========================================================
def get_request_session_key(request):
    """
    دریافت session_key از query params، body یا session جنگو.
    """

    session_key = request.query_params.get("session_key")

    if not session_key:
        session_key = request.data.get("session_key")

    if not request.session.session_key:
        request.session.create()

    if not session_key:
        session_key = request.session.session_key

    return session_key


def merge_guest_cart_into_user_cart(
    guest_cart,
    user_cart,
):
    """
    انتقال آیتم‌های سبد مهمان به سبد کاربر.

    تعداد نهایی بیشتر از موجودی یا سقف مجاز نخواهد شد.
    """

    with transaction.atomic():
        guest_items = guest_cart.items.select_related(
            "variant",
            "variant__product",
        )

        for guest_item in guest_items:
            user_item, created = CartItem.objects.get_or_create(
                cart=user_cart,
                variant=guest_item.variant,
                defaults={
                    "quantity": min(
                        guest_item.quantity,
                        guest_item.variant.stock,
                        MAX_CART_ITEM_QUANTITY,
                    ),
                },
            )

            if not created:
                new_quantity = (
                    user_item.quantity
                    + guest_item.quantity
                )

                allowed_quantity = min(
                    new_quantity,
                    guest_item.variant.stock,
                    MAX_CART_ITEM_QUANTITY,
                )

                if user_item.quantity != allowed_quantity:
                    user_item.quantity = allowed_quantity
                    user_item.save(
                        update_fields=["quantity"],
                    )

        guest_cart.is_active = False
        guest_cart.save(
            update_fields=["is_active"],
        )


def get_user_cart(request):
    """
    دریافت سبد خرید کاربر یا مهمان.

    اگر کاربر وارد حساب شده باشد و سبد مهمان فعالی
    با session_key ارسالی وجود داشته باشد، سبد مهمان
    در سبد کاربر ادغام می‌شود.
    """

    session_key = get_request_session_key(request)

    # کاربر واردشده
    if request.user.is_authenticated:
        user_cart, _ = Cart.objects.get_or_create(
            user=request.user,
            is_active=True,
        )

        guest_cart = (
            Cart.objects
            .filter(
                session_key=session_key,
                user__isnull=True,
                is_active=True,
            )
            .exclude(pk=user_cart.pk)
            .first()
        )

        if guest_cart:
            merge_guest_cart_into_user_cart(
                guest_cart=guest_cart,
                user_cart=user_cart,
            )

        return user_cart

    # کاربر مهمان
    guest_cart, _ = Cart.objects.get_or_create(
        session_key=session_key,
        user=None,
        is_active=True,
    )

    return guest_cart


def cart_response_data(
    cart,
    request,
):
    """
    سریالایز کردن سبد خرید همراه با context درخواست.
    """

    return CartSerializer(
        cart,
        context={
            "request": request,
        },
    ).data


# =========================================================
# فروش‌های لحظه‌ای
# =========================================================
class FlashSalesView(APIView):
    """
    دریافت محصولات دارای فروش لحظه‌ای فعال.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        products = (
            Product.objects
            .filter(
                flash_sale=True,
                flash_sale_end__gt=timezone.now(),
                is_active=True,
            )
            .distinct()
        )

        serializer = ProductListSerializer(
            products,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            {
                "count": products.count(),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# ذخیره سبد خرید
# =========================================================
class SaveCartView(APIView):
    """
    ذخیره سبد خرید برای کاربر.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart = get_user_cart(request)

        return Response(
            {
                "message": "سبد خرید ذخیره شد.",
                "cart": cart_response_data(
                    cart=cart,
                    request=request,
                ),
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# بازیابی سبد ذخیره‌شده
# =========================================================
class LoadSavedCartView(APIView):
    """
    بازیابی سبد خرید کاربر.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = get_user_cart(request)

        return Response(
            {
                "cart": cart_response_data(
                    cart=cart,
                    request=request,
                ),
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# پیگیری سفارش
# =========================================================
class TrackOrderView(APIView):
    """
    پیگیری سفارش با کد رهگیری.
    """

    permission_classes = [AllowAny]

    def get(self, request, tracking_code):
        order = get_object_or_404(
            Order,
            tracking_code=tracking_code,
        )

        serializer = OrderSerializer(
            order,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


# =========================================================
# درخواست مرجوعی
# =========================================================
class ReturnRequestView(APIView):
    """
    ثبت درخواست مرجوعی کالا.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response(
            {
                "message": "درخواست مرجوعی ثبت شد.",
            },
            status=status.HTTP_201_CREATED,
        )


# =========================================================
# پیشنهادهای ویژه
# =========================================================
class SpecialOffersView(APIView):
    """
    دریافت محصولات دارای واریانت تخفیف‌خورده.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        products = (
            Product.objects
            .filter(
                variants__discount_price__isnull=False,
                is_special=True,
                is_active=True,
            )
            .distinct()[:10]
        )

        serializer = ProductListSerializer(
            products,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            {
                "count": len(products),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# پرفروش‌ترین محصولات هفته
# =========================================================
class WeeklyBestSellersAPIView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    pagination_class = CustomCategoryPagination
    permission_classes = [AllowAny]

    def get_queryset(self):
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)

        sales_queryset = (
            SalesSummary.objects
            .filter(
                created_at__date__range=(
                    week_ago,
                    today,
                ),
            )
            .values("product_id")
            .annotate(
                total_sold=Sum("total_quantity"),
            )
            .order_by("-total_sold")
        )

        product_ids = [
            item["product_id"]
            for item in sales_queryset
        ]

        if not product_ids:
            return (
                Product.objects
                .filter(is_active=True)
                .order_by("-created_at")
            )

        preserved_order = Case(
            *[
                When(
                    id=product_id,
                    then=position,
                )
                for position, product_id
                in enumerate(product_ids)
            ],
            output_field=IntegerField(),
        )

        return (
            Product.objects
            .filter(
                id__in=product_ids,
                is_active=True,
            )
            .order_by(preserved_order)
        )

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.get_serializer(
                    page,
                    many=True,
                    context={
                        "request": request,
                    },
                )

                return self.get_paginated_response(
                    serializer.data,
                )

            serializer = self.get_serializer(
                queryset,
                many=True,
                context={
                    "request": request,
                },
            )

            return Response(
                {
                    "success": True,
                    "data": serializer.data,
                    "count": queryset.count(),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as error:
            return Response(
                {
                    "success": False,
                    "message": "خطا در دریافت اطلاعات.",
                    "error": str(error),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# =========================================================
# مشاهده سبد خرید
# =========================================================
class CartView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        return get_user_cart(self.request)


# =========================================================
# افزودن آیتم به سبد خرید
# =========================================================
class AddToCartView(generics.GenericAPIView):
    serializer_class = CartItemCreateSerializer
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        input_serializer = self.get_serializer(
            data=request.data,
        )
        input_serializer.is_valid(
            raise_exception=True,
        )

        variant_id = input_serializer.validated_data[
            "variant_id"
        ]
        quantity = input_serializer.validated_data[
            "quantity"
        ]

        if quantity > MAX_CART_ITEM_QUANTITY:
            return Response(
                {
                    "error": (
                        f"حداکثر تعداد مجاز "
                        f"{MAX_CART_ITEM_QUANTITY} عدد است."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        variant = get_object_or_404(
            ProductVariant.objects.select_related(
                "product",
            ),
            id=variant_id,
        )

        if variant.stock <= 0:
            return Response(
                {
                    "error": "این کالا در حال حاضر ناموجود است.",
                    "available_stock": 0,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart = get_user_cart(request)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            variant=variant,
            defaults={
                "quantity": quantity,
            },
        )

        if created:
            final_quantity = quantity
        else:
            final_quantity = (
                cart_item.quantity
                + quantity
            )

        if final_quantity > variant.stock:
            available_to_add = max(
                variant.stock - cart_item.quantity,
                0,
            )

            # اگر آیتم تازه ایجاد شده بود ولی موجودی کافی نبود،
            # آن را حذف می‌کنیم.
            if created:
                cart_item.delete()

            return Response(
                {
                    "error": (
                        "موجودی کافی نیست. "
                        f"حداکثر {available_to_add} عدد دیگر "
                        "می‌توانید اضافه کنید."
                    ),
                    "available_stock": variant.stock,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if final_quantity > MAX_CART_ITEM_QUANTITY:
            if created:
                cart_item.delete()

            return Response(
                {
                    "error": (
                        f"حداکثر تعداد مجاز "
                        f"{MAX_CART_ITEM_QUANTITY} عدد است."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not created:
            cart_item.quantity = final_quantity
            cart_item.save(
                update_fields=["quantity"],
            )

        return Response(
            {
                "message": (
                    "آیتم با موفقیت به سبد خرید افزوده شد."
                ),
                "item": CartItemSerializer(
                    cart_item,
                    context={
                        "request": request,
                    },
                ).data,
                "cart": cart_response_data(
                    cart=cart,
                    request=request,
                ),
            },
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )


# =========================================================
# بروزرسانی تعداد آیتم سبد خرید
# =========================================================
class UpdateCartItemView(generics.GenericAPIView):
    serializer_class = CartItemUpdateSerializer
    permission_classes = [AllowAny]

    def put(self, request, pk):
        return self.update_cart_item(
            request=request,
            pk=pk,
        )

    def patch(self, request, pk):
        return self.update_cart_item(
            request=request,
            pk=pk,
        )

    @transaction.atomic
    def update_cart_item(self, request, pk):
        input_serializer = self.get_serializer(
            data=request.data,
        )
        input_serializer.is_valid(
            raise_exception=True,
        )

        quantity = input_serializer.validated_data[
            "quantity"
        ]

        if quantity > MAX_CART_ITEM_QUANTITY:
            return Response(
                {
                    "error": (
                        f"حداکثر تعداد مجاز "
                        f"{MAX_CART_ITEM_QUANTITY} عدد است."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart = get_user_cart(request)

        cart_item = get_object_or_404(
            CartItem.objects.select_related(
                "variant",
                "variant__product",
            ),
            id=pk,
            cart=cart,
        )

        if quantity > cart_item.variant.stock:
            return Response(
                {
                    "error": (
                        f"فقط {cart_item.variant.stock} "
                        "عدد موجود است."
                    ),
                    "available_stock": (
                        cart_item.variant.stock
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart_item.quantity = quantity
        cart_item.save(
            update_fields=["quantity"],
        )

        return Response(
            {
                "message": "تعداد آیتم بروزرسانی شد.",
                "item": CartItemSerializer(
                    cart_item,
                    context={
                        "request": request,
                    },
                ).data,
                "cart": cart_response_data(
                    cart=cart,
                    request=request,
                ),
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# حذف آیتم از سبد خرید
# =========================================================
class RemoveCartItemView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def delete(self, request, pk):
        cart = get_user_cart(request)

        cart_item = get_object_or_404(
            CartItem,
            id=pk,
            cart=cart,
        )

        cart_item.delete()

        return Response(
            {
                "message": "آیتم از سبد خرید حذف شد.",
                "cart": cart_response_data(
                    cart=cart,
                    request=request,
                ),
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# خالی کردن سبد خرید
# =========================================================
class ClearCartView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def delete(self, request):
        cart = get_user_cart(request)
        cart.items.all().delete()

        return Response(
            {
                "message": (
                    "سبد خرید با موفقیت خالی شد."
                ),
                "cart": cart_response_data(
                    cart=cart,
                    request=request,
                ),
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# ایجاد سفارش از سبد خرید
# =========================================================
class CreateOrderView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        cart = get_user_cart(request)

        cart_items = list(
            cart.items.select_related(
                "variant",
                "variant__product",
            )
        )

        if not cart_items:
            return Response(
                {
                    "error": "سبد خرید خالی است.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # بررسی موجودی تمام آیتم‌ها پیش از ساخت سفارش
        for item in cart_items:
            if item.variant.stock < item.quantity:
                return Response(
                    {
                        "error": (
                            f"محصول "
                            f"{item.variant.product.name} "
                            f"تنها {item.variant.stock} "
                            "عدد موجود است."
                        ),
                        "variant_id": item.variant_id,
                        "available_stock": (
                            item.variant.stock
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        total_price = cart.total_price()

        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            status="pending",
        )

        order_items = []

        for item in cart_items:
            order_items.append(
                OrderItem(
                    order=order,
                    variant=item.variant,
                    quantity=item.quantity,
                    price=item.price(),
                )
            )

            item.variant.stock -= item.quantity
            item.variant.save(
                update_fields=["stock"],
            )

        OrderItem.objects.bulk_create(
            order_items,
        )

        cart.items.all().delete()

        order_serializer = OrderSerializer(
            order,
            context={
                "request": request,
            },
        )

        return Response(
            {
                "message": "سفارش با موفقیت ثبت شد.",
                "order": order_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


# =========================================================
# لیست سفارش‌های کاربر
# =========================================================
class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects
            .filter(user=self.request.user)
            .order_by("-created_at")
        )


# =========================================================
# جزئیات یک سفارش
# =========================================================
class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user,
        )


# =========================================================
# لغو سفارش
# =========================================================
class CancelOrderView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        order = get_object_or_404(
            Order.objects.prefetch_related(
                "items__variant",
            ),
            id=pk,
            user=request.user,
        )

        if order.status != "pending":
            return Response(
                {
                    "error": (
                        "این سفارش دیگر قابل لغو نیست."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        for item in order.items.all():
            item.variant.stock += item.quantity
            item.variant.save(
                update_fields=["stock"],
            )

        order.status = "cancelled"
        order.save(
            update_fields=["status"],
        )

        return Response(
            {
                "message": (
                    "سفارش با موفقیت لغو شد."
                ),
                "order": OrderSerializer(
                    order,
                    context={
                        "request": request,
                    },
                ).data,
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# ادغام دستی سبد مهمان با سبد کاربر
# =========================================================
class MergeCartView(APIView):
    """
    ادغام سبد خرید مهمان با حساب کاربری.

    POST /api/orders/cart/merge/

    Body:
    {
        "session_key": "abc123"
    }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_key = request.data.get(
            "session_key",
        )

        if not session_key:
            return Response(
                {
                    "error": "session_key الزامی است.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        guest_cart = (
            Cart.objects
            .filter(
                session_key=session_key,
                user__isnull=True,
                is_active=True,
            )
            .first()
        )

        user_cart, _ = Cart.objects.get_or_create(
            user=request.user,
            is_active=True,
        )

        if not guest_cart:
            return Response(
                {
                    "message": (
                        "سبد خرید مهمان فعالی یافت نشد."
                    ),
                    "items_moved": 0,
                    "cart": cart_response_data(
                        cart=user_cart,
                        request=request,
                    ),
                },
                status=status.HTTP_200_OK,
            )

        guest_items_count = guest_cart.items.count()

        merge_guest_cart_into_user_cart(
            guest_cart=guest_cart,
            user_cart=user_cart,
        )

        return Response(
            {
                "message": (
                    f"{guest_items_count} آیتم با موفقیت "
                    "به سبد خرید شما منتقل شد."
                ),
                "items_moved": guest_items_count,
                "cart": cart_response_data(
                    cart=user_cart,
                    request=request,
                ),
            },
            status=status.HTTP_200_OK,
        )
