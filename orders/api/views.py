# orders/api/views.py

from datetime import timedelta
from decimal import Decimal, InvalidOperation

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
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bazbia_packing.services.fixed_shipping_quote_service import (
    FixedShippingQuoteService,
)
from customers.models import CustomerAddress
from orders.api.serializers import (
    CartItemCreateSerializer,
    CartItemSerializer,
    CartItemUpdateSerializer,
    CartSerializer,
    CreateOrderSerializer,
    OrderSerializer,
)
from orders.models import (
    Cart,
    CartItem,
    Order,
    OrderItem,
    OrderItemCostAllocation,
    SalesSummary,
)
from products.api.pagination import CustomCategoryPagination
from products.api.serializers import ProductListSerializer
from products.models import Product, ProductVariant
from products.services.variant_stock import (
    calculate_variant_available_stock,
)
from suppliers.models import SupplierOffer


MAX_CART_ITEM_QUANTITY = 100


# =========================================================
# توابع کمکی عمومی
# =========================================================
def get_request_session_key(request) -> str:
    session_key = request.query_params.get("session_key")

    if not session_key:
        session_key = request.data.get("session_key")

    if not request.session.session_key:
        request.session.create()

    if not session_key:
        session_key = request.session.session_key

    return session_key


def get_or_create_user_cart(user) -> Cart:
    cart, _ = Cart.objects.get_or_create(
        user=user,
        defaults={"is_active": True},
    )

    if not cart.is_active:
        cart.is_active = True
        cart.save(update_fields=["is_active"])

    return cart


def get_user_cart(request) -> Cart:
    if request.user.is_authenticated:
        return get_or_create_user_cart(request.user)

    session_key = get_request_session_key(request)

    guest_cart, _ = Cart.objects.get_or_create(
        session_key=session_key,
        user=None,
        is_active=True,
    )

    return guest_cart


def cart_response_data(cart: Cart, request) -> dict:
    return CartSerializer(
        cart,
        context={"request": request},
    ).data


def get_variant_unit_price(
    variant: ProductVariant,
) -> Decimal:
    if variant.discount_price is not None:
        return variant.discount_price

    return variant.price


def decimal_from_value(
    value,
    default: Decimal = Decimal("0"),
) -> Decimal:
    try:
        return Decimal(str(value))
    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ):
        return default


def build_address_snapshot(
    address: CustomerAddress,
) -> dict:
    return {
        "address_id": address.id,
        "title": address.title,
        "recipient_name": address.recipient_name,
        "recipient_phone": address.recipient_phone,
        "province": address.province,
        "city": address.city,
        "address": address.address,
        "postal_code": address.postal_code,
    }


def merge_guest_cart_into_user_cart(
    guest_cart: Cart,
    user_cart: Cart,
) -> None:
    guest_items = guest_cart.items.select_related(
        "variant",
        "variant__product",
    )

    for guest_item in guest_items:
        available_stock = calculate_variant_available_stock(
            guest_item.variant
        )

        allowed_guest_quantity = min(
            guest_item.quantity,
            available_stock,
            MAX_CART_ITEM_QUANTITY,
        )

        if allowed_guest_quantity <= 0:
            continue

        user_item, created = CartItem.objects.get_or_create(
            cart=user_cart,
            variant=guest_item.variant,
            defaults={
                "quantity": allowed_guest_quantity,
            },
        )

        if created:
            continue

        new_quantity = (
            user_item.quantity
            + guest_item.quantity
        )

        allowed_quantity = min(
            new_quantity,
            available_stock,
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


# =========================================================
# فروش‌های لحظه‌ای
# =========================================================
class FlashSalesView(APIView):
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
            context={"request": request},
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
    permission_classes = [AllowAny]

    def get(self, request, tracking_code):
        order = get_object_or_404(
            Order,
            tracking_code=tracking_code,
        )

        serializer = OrderSerializer(
            order,
            context={"request": request},
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


# =========================================================
# درخواست مرجوعی
# =========================================================
class ReturnRequestView(APIView):
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
            context={"request": request},
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
class WeeklyBestSellersAPIView(
    generics.ListAPIView
):
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

    def list(
        self,
        request,
        *args,
        **kwargs,
    ):
        try:
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.get_serializer(
                    page,
                    many=True,
                    context={"request": request},
                )

                return self.get_paginated_response(
                    serializer.data
                )

            serializer = self.get_serializer(
                queryset,
                many=True,
                context={"request": request},
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
    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
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
                        f"{MAX_CART_ITEM_QUANTITY} "
                        "عدد است."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        variant = get_object_or_404(
            ProductVariant.objects.select_related(
                "product"
            ),
            id=variant_id,
        )

        available_stock = (
            calculate_variant_available_stock(
                variant
            )
        )

        if available_stock <= 0:
            return Response(
                {
                    "error": (
                        "این کالا در حال حاضر "
                        "ناموجود است."
                    ),
                    "available_stock": 0,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart = get_user_cart(request)

        cart_item, created = (
            CartItem.objects.get_or_create(
                cart=cart,
                variant=variant,
                defaults={"quantity": quantity},
            )
        )

        final_quantity = (
            quantity
            if created
            else cart_item.quantity + quantity
        )

        if final_quantity > available_stock:
            current_cart_quantity = (
                0
                if created
                else cart_item.quantity
            )

            available_to_add = max(
                available_stock
                - current_cart_quantity,
                0,
            )

            if created:
                cart_item.delete()

            return Response(
                {
                    "error": (
                        "موجودی کافی نیست. "
                        f"حداکثر "
                        f"{available_to_add} "
                        "عدد دیگر می‌توانید "
                        "اضافه کنید."
                    ),
                    "available_stock": available_stock,
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
                        f"{MAX_CART_ITEM_QUANTITY} "
                        "عدد است."
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
                    "آیتم با موفقیت به "
                    "سبد خرید افزوده شد."
                ),
                "item": CartItemSerializer(
                    cart_item,
                    context={"request": request},
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
class UpdateCartItemView(
    generics.GenericAPIView
):
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
    def update_cart_item(
        self,
        request,
        pk,
    ):
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
                        f"{MAX_CART_ITEM_QUANTITY} "
                        "عدد است."
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

        available_stock = (
            calculate_variant_available_stock(
                cart_item.variant
            )
        )

        if quantity > available_stock:
            return Response(
                {
                    "error": (
                        f"فقط {available_stock} "
                        "عدد موجود است."
                    ),
                    "available_stock": available_stock,
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
                    context={"request": request},
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
class RemoveCartItemView(
    generics.GenericAPIView
):
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
# خالی‌کردن سبد خرید
# =========================================================
class ClearCartView(
    generics.GenericAPIView
):
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
class CreateOrderView(
    generics.GenericAPIView
):
    permission_classes = [IsAuthenticated]
    serializer_class = CreateOrderSerializer

    @transaction.atomic
    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        input_serializer = self.get_serializer(
            data=request.data,
        )

        input_serializer.is_valid(
            raise_exception=True,
        )

        validated_data = (
            input_serializer.validated_data
        )

        address_id = validated_data["address_id"]
        shipping_quote_id = validated_data[
            "shipping_quote_id"
        ]
        shipping_method_code = validated_data[
            "shipping_method_code"
        ]
        payment_method = validated_data[
            "payment_method"
        ]

        customer = getattr(
            request.user,
            "customer_profile",
            None,
        )

        if customer is None:
            return Response(
                {
                    "error": (
                        "پروفایل مشتری برای "
                        "این کاربر یافت نشد."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        address = get_object_or_404(
            CustomerAddress,
            id=address_id,
            customer=customer,
        )

        cart = get_user_cart(request)

        cart = (
            Cart.objects
            .select_for_update()
            .get(pk=cart.pk)
        )

        cart_items = list(
            cart.items.select_related(
                "variant",
                "variant__product",
            )
        )

        if not cart_items:
            return Response(
                {"error": "سبد خرید خالی است."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        variant_ids = [
            item.variant_id
            for item in cart_items
        ]

        locked_variants = {
            variant.id: variant
            for variant in (
                ProductVariant.objects
                .select_for_update()
                .select_related("product")
                .filter(id__in=variant_ids)
            )
        }

        items_total = Decimal("0")
        order_items_data = []

        for cart_item in cart_items:
            variant = locked_variants.get(
                cart_item.variant_id
            )

            if variant is None:
                return Response(
                    {
                        "error": (
                            "یکی از کالاهای "
                            "سبد خرید دیگر "
                            "در دسترس نیست."
                        ),
                        "variant_id":
                            cart_item.variant_id,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            available_stock = (
                calculate_variant_available_stock(
                    variant
                )
            )

            if available_stock < cart_item.quantity:
                return Response(
                    {
                        "error": (
                            f"محصول "
                            f"{variant.product.name} "
                            f"فقط {available_stock} "
                            "عدد موجودی قابل سفارش دارد."
                        ),
                        "variant_id": variant.id,
                        "available_stock":
                            available_stock,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            unit_price = get_variant_unit_price(
                variant
            )

            line_total = (
                unit_price
                * cart_item.quantity
            )

            items_total += line_total

            order_items_data.append(
                {
                    "variant": variant,
                    "quantity":
                        cart_item.quantity,
                    "price": unit_price,
                }
            )

        shipping_quote = (
            FixedShippingQuoteService(
                cart=cart,
                address=address,
            ).calculate()
        )

        available_methods = shipping_quote.get(
            "methods",
            [],
        )

        selected_method = next(
            (
                method
                for method in available_methods
                if method.get("code")
                == shipping_method_code
            ),
            None,
        )

        if selected_method is None:
            return Response(
                {
                    "error": (
                        "روش ارسال انتخاب‌شده "
                        "معتبر یا فعال نیست."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        shipping_cost = decimal_from_value(
            selected_method.get("cost", 0)
        )

        shipping_method_title = str(
            selected_method.get("title", "")
        ).strip()

        address_snapshot = (
            build_address_snapshot(address)
        )

        order = Order.objects.create(
            user=request.user,
            status=Order.STATUS_PENDING,
            shipping_address=address,
            shipping_address_snapshot=(
                address_snapshot
            ),
            shipping_method_code=(
                shipping_method_code
            ),
            shipping_method_title=(
                shipping_method_title
            ),
            shipping_quote_id=(
                shipping_quote_id
            ),
            payment_method=payment_method,
            items_total=items_total,
            shipping_cost=shipping_cost,
            discount_amount=Decimal("0"),
        )

        order_items_map = {}

        for data in order_items_data:
          order_item = OrderItem.objects.create(
            order=order,
            variant=data["variant"],
            quantity=data["quantity"],
            price=data["price"],
        )

          order_items_map[
          data["variant"].id
           ] = order_item
        
        
        
        # ---------------------------------------------
        # ۱۱. کم‌کردن موجودی
        #
        # ترتیب مصرف:
        # ۱. موجودی داخلی variant.stock
        # ۲. موجودی SupplierOffer
        # ---------------------------------------------
        for data in order_items_data:
            variant = data["variant"]
            remaining_quantity = int(
                data["quantity"]
            )

            internal_stock = max(
                int(variant.stock or 0),
                0,
            )

            internal_deduction = min(
                internal_stock,
                remaining_quantity,
            )

            if internal_deduction > 0:
                variant.stock = (
                    internal_stock
                    - internal_deduction
                )

                variant.save(
                    update_fields=["stock"],
                )

                remaining_quantity -= (
                    internal_deduction
                )

                order_item = order_items_map [variant.id]

                OrderItemCostAllocation.objects.create(
                  order_item=order_item,
                  source_type=(OrderItemCostAllocation.SOURCE_INTERNAL),
                  quantity=internal_deduction,
                  unit_cost=None,
                    ) 


            if remaining_quantity <= 0:
                continue

            supplier_offers = (
                SupplierOffer.objects
                .select_for_update()
                .filter(
                    variant=variant,
                    is_available=True,
                    supplier_stock__gt=0,
                )
                .order_by(
                    "-is_primary",
                    "id",
                )
            )

            for offer in supplier_offers:
                if remaining_quantity <= 0:
                    break

                offer_stock = max(
                    int(
                        offer.supplier_stock
                        or 0
                    ),
                    0,
                )

                supplier_deduction = min(
                    offer_stock,
                    remaining_quantity,
                )

                if supplier_deduction <= 0:
                    continue

                order_item = order_items_map[variant.id]
                OrderItemCostAllocation.objects.create(   
                  order_item=order_item,
                  source_type=(OrderItemCostAllocation.SOURCE_SUPPLIER),
                  quantity=supplier_deduction,
                  unit_cost=offer.purchase_price,
                  supplier=offer.supplier,
                  supplier_offer=offer,
                      )


                offer.supplier_stock = (
                    offer_stock
                    - supplier_deduction
                )

                update_fields = [
                    "supplier_stock",
                ]

                if offer.supplier_stock <= 0:
                    offer.supplier_stock = 0
                    offer.is_available = False
                    update_fields.append(
                        "is_available"
                    )

                offer.save(
                    update_fields=update_fields,
                )

                remaining_quantity -= (
                    supplier_deduction
                )

            if remaining_quantity > 0:
                raise ValueError(
                    (
                        "موجودی قابل سفارش "
                        f"واریانت {variant.id} "
                        "هنگام کسر موجودی "
                        f"{remaining_quantity} عدد "
                        "کمتر از مقدار مورد "
                        "انتظار بود."
                    )
                )

        cart.items.all().delete()

        output_serializer = OrderSerializer(
            order,
            context={"request": request},
        )

        return Response(
            {
                "message": (
                    "سفارش با موفقیت ثبت شد."
                ),
                "order": output_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


# =========================================================
# لیست سفارش‌های کاربر
# =========================================================
class OrderListView(
    generics.ListAPIView
):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects
            .filter(user=self.request.user)
            .prefetch_related(
                "items__variant",
                "items__variant__product",
            )
            .order_by("-created_at")
        )


# =========================================================
# جزئیات یک سفارش
# =========================================================
class OrderDetailView(
    generics.RetrieveAPIView
):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects
            .filter(user=self.request.user)
            .prefetch_related(
                "items__variant",
                "items__variant__product",
            )
        )


# =========================================================
# لغو سفارش
# =========================================================
class CancelOrderView(
    generics.GenericAPIView
):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        order = get_object_or_404(
            Order.objects
            .select_for_update()
            .prefetch_related(
                "items__variant",
            ),
            id=pk,
            user=request.user,
        )

        if order.status != Order.STATUS_PENDING:
            return Response(
                {
                    "error": (
                        "این سفارش دیگر "
                        "قابل لغو نیست."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        order_items = list(
            order.items.all()
        )

        variant_ids = [
            item.variant_id
            for item in order_items
        ]

        locked_variants = {
            variant.id: variant
            for variant in (
                ProductVariant.objects
                .select_for_update()
                .filter(id__in=variant_ids)
            )
        }

        for item in order_items:
            variant = locked_variants.get(
                item.variant_id
            )

            if variant is None:
                continue

            variant.stock += item.quantity
            variant.save(
                update_fields=["stock"],
            )

        order.status = Order.STATUS_CANCELLED
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
                    context={"request": request},
                ).data,
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# ادغام سبد مهمان با سبد کاربر
# =========================================================
class MergeCartView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        session_key = str(
            request.data.get(
                "session_key",
                "",
            )
        ).strip()

        if not session_key:
            return Response(
                {
                    "error":
                        "session_key الزامی است.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        guest_cart = (
            Cart.objects
            .select_for_update()
            .filter(
                session_key=session_key,
                user__isnull=True,
                is_active=True,
            )
            .first()
        )

        user_cart = get_or_create_user_cart(
            request.user
        )

        if guest_cart is None:
            return Response(
                {
                    "message": (
                        "سبد خرید مهمان "
                        "فعالی یافت نشد."
                    ),
                    "items_moved": 0,
                    "cart": cart_response_data(
                        cart=user_cart,
                        request=request,
                    ),
                },
                status=status.HTTP_200_OK,
            )

        guest_items_count = (
            guest_cart.items.count()
        )

        merge_guest_cart_into_user_cart(
            guest_cart=guest_cart,
            user_cart=user_cart,
        )

        return Response(
            {
                "message": (
                    f"{guest_items_count} آیتم "
                    "با موفقیت به سبد خرید "
                    "شما منتقل شد."
                ),
                "items_moved":
                    guest_items_count,
                "cart": cart_response_data(
                    cart=user_cart,
                    request=request,
                ),
            },
            status=status.HTTP_200_OK,
        )
