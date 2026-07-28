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
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
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
    SalesSummary,
)
from products.api.pagination import (
    CustomCategoryPagination,
)
from products.api.serializers import (
    ProductListSerializer,
)
from products.models import (
    Product,
    ProductVariant,
)


# حداکثر تعداد مجاز از هر واریانت در سبد خرید
MAX_CART_ITEM_QUANTITY = 10


# =========================================================
# توابع کمکی عمومی
# =========================================================
def get_request_session_key(request) -> str:
    """
    دریافت کلید سشن مشتری مهمان.

    ترتیب بررسی:
    1. Query Parameter
    2. Request Body
    3. Session داخلی Django

    در صورتی که سشن هنوز ایجاد نشده باشد، یک سشن جدید
    ساخته می‌شود.
    """

    session_key = request.query_params.get(
        "session_key"
    )

    if not session_key:
        session_key = request.data.get(
            "session_key"
        )

    if not request.session.session_key:
        request.session.create()

    if not session_key:
        session_key = (
            request.session.session_key
        )

    return session_key


def get_or_create_user_cart(user) -> Cart:
    """
    دریافت سبد خرید کاربر واردشده.

    چون فیلد user در مدل Cart از نوع OneToOneField است،
    نباید user و is_active هم‌زمان در get_or_create
    استفاده شوند؛ زیرا ممکن است سبد غیرفعال قبلی وجود
    داشته باشد و ساخت سبد جدید باعث خطای Unique شود.

    در صورت غیرفعال بودن سبد قبلی، همان سبد دوباره فعال
    می‌شود.
    """

    cart, _ = Cart.objects.get_or_create(
        user=user,
        defaults={
            "is_active": True,
        },
    )

    if not cart.is_active:
        cart.is_active = True
        cart.save(
            update_fields=["is_active"],
        )

    return cart


def get_user_cart(request) -> Cart:
    """
    دریافت یا ایجاد سبد خرید مناسب درخواست.

    برای کاربر واردشده، سبد متصل به حساب کاربری خوانده
    می‌شود.

    برای کاربر مهمان، سبد براساس session_key خوانده یا
    ساخته می‌شود.

    ادغام سبد مهمان و کاربر فقط از طریق MergeCartView
    انجام می‌شود.
    """

    if request.user.is_authenticated:
        return get_or_create_user_cart(
            request.user
        )

    session_key = get_request_session_key(
        request
    )

    guest_cart, _ = Cart.objects.get_or_create(
        session_key=session_key,
        user=None,
        is_active=True,
    )

    return guest_cart


def cart_response_data(
    cart: Cart,
    request,
) -> dict:
    """
    سریالایز کردن سبد خرید همراه با context درخواست.
    """

    return CartSerializer(
        cart,
        context={
            "request": request,
        },
    ).data


def get_variant_unit_price(
    variant: ProductVariant,
) -> Decimal:
    """
    دریافت قیمت نهایی یک واحد واریانت.

    در صورت وجود discount_price، قیمت تخفیف‌خورده
    استفاده می‌شود؛ در غیر این صورت قیمت اصلی واریانت
    استفاده خواهد شد.

    تمام مبلغ‌ها در پروژه بازبیا بر حسب تومان هستند.
    """

    if variant.discount_price is not None:
        return variant.discount_price

    return variant.price


def decimal_from_value(
    value,
    default: Decimal = Decimal("0"),
) -> Decimal:
    """
    تبدیل امن مقدار دریافتی به Decimal.

    برای جلوگیری از خطاهای ناشی از float یا مقدار None،
    ابتدا مقدار به رشته تبدیل می‌شود.
    """

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
    """
    ساخت نسخه ثابت آدرس سفارش.

    آدرس حساب مشتری ممکن است بعداً ویرایش یا حذف شود؛
    بنابراین اطلاعات کامل تحویل در لحظه ثبت سفارش داخل
    خود سفارش ذخیره می‌شود.
    """

    return {
        "address_id": address.id,
        "title": address.title,
        "recipient_name":
            address.recipient_name,
        "recipient_phone":
            address.recipient_phone,
        "province": address.province,
        "city": address.city,
        "address": address.address,
        "postal_code":
            address.postal_code,
    }


def merge_guest_cart_into_user_cart(
    guest_cart: Cart,
    user_cart: Cart,
) -> None:
    """
    انتقال آیتم‌های سبد مهمان به سبد کاربر.

    تعداد نهایی هر آیتم از موجودی کالا و سقف مجاز سبد
    بیشتر نخواهد شد.
    """

    guest_items = (
        guest_cart.items
        .select_related(
            "variant",
            "variant__product",
        )
    )

    for guest_item in guest_items:
        allowed_guest_quantity = min(
            guest_item.quantity,
            guest_item.variant.stock,
            MAX_CART_ITEM_QUANTITY,
        )

        if allowed_guest_quantity <= 0:
            continue

        user_item, created = (
            CartItem.objects.get_or_create(
                cart=user_cart,
                variant=guest_item.variant,
                defaults={
                    "quantity":
                        allowed_guest_quantity,
                },
            )
        )

        if created:
            continue

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
            user_item.quantity = (
                allowed_quantity
            )

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
    """
    دریافت محصولات دارای فروش لحظه‌ای فعال.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        products = (
            Product.objects
            .filter(
                flash_sale=True,
                flash_sale_end__gt=
                    timezone.now(),
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
    ذخیره سبد خرید کاربر واردشده.
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
    بازیابی سبد خرید کاربر واردشده.
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

    توجه:
    مدل Order باید فیلد tracking_code داشته باشد.
    در غیر این صورت این endpoint باید تا زمان اضافه‌شدن
    فیلد رهگیری غیرفعال شود.
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

    فعلاً فقط پاسخ اولیه برمی‌گرداند و بعداً باید به مدل
    درخواست مرجوعی متصل شود.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response(
            {
                "message":
                    "درخواست مرجوعی ثبت شد.",
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
                variants__discount_price__isnull=
                    False,
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
class WeeklyBestSellersAPIView(
    generics.ListAPIView
):
    """
    دریافت محصولات پرفروش هفت روز اخیر.
    """

    serializer_class = (
        ProductListSerializer
    )

    pagination_class = (
        CustomCategoryPagination
    )

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
                total_sold=Sum(
                    "total_quantity"
                ),
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

            page = self.paginate_queryset(
                queryset
            )

            if page is not None:
                serializer = (
                    self.get_serializer(
                        page,
                        many=True,
                        context={
                            "request":
                                request,
                        },
                    )
                )

                return (
                    self.get_paginated_response(
                        serializer.data
                    )
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
                    "count":
                        queryset.count(),
                },
                status=
                    status.HTTP_200_OK,
            )

        except Exception as error:
            return Response(
                {
                    "success": False,
                    "message":
                        "خطا در دریافت اطلاعات.",
                    "error": str(error),
                },
                status=(
                    status
                    .HTTP_500_INTERNAL_SERVER_ERROR
                ),
            )


# =========================================================
# مشاهده سبد خرید
# =========================================================
class CartView(generics.RetrieveAPIView):
    """
    دریافت سبد خرید فعلی کاربر یا مهمان.
    """

    serializer_class = CartSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        return get_user_cart(
            self.request
        )


# =========================================================
# افزودن آیتم به سبد خرید
# =========================================================
class AddToCartView(
    generics.GenericAPIView
):
    """
    افزودن یک واریانت به سبد خرید.
    """

    serializer_class = (
        CartItemCreateSerializer
    )

    permission_classes = [AllowAny]

    @transaction.atomic
    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        input_serializer = (
            self.get_serializer(
                data=request.data,
            )
        )

        input_serializer.is_valid(
            raise_exception=True,
        )

        variant_id = (
            input_serializer
            .validated_data["variant_id"]
        )

        quantity = (
            input_serializer
            .validated_data["quantity"]
        )

        if quantity > MAX_CART_ITEM_QUANTITY:
            return Response(
                {
                    "error": (
                        f"حداکثر تعداد مجاز "
                        f"{MAX_CART_ITEM_QUANTITY} "
                        "عدد است."
                    ),
                },
                status=
                    status.HTTP_400_BAD_REQUEST,
            )

        variant = get_object_or_404(
            ProductVariant.objects
            .select_related("product"),
            id=variant_id,
        )

        if variant.stock <= 0:
            return Response(
                {
                    "error":
                        "این کالا در حال حاضر ناموجود است.",
                    "available_stock": 0,
                },
                status=
                    status.HTTP_400_BAD_REQUEST,
            )

        cart = get_user_cart(request)

        cart_item, created = (
            CartItem.objects.get_or_create(
                cart=cart,
                variant=variant,
                defaults={
                    "quantity": quantity,
                },
            )
        )

        final_quantity = (
            quantity
            if created
            else (
                cart_item.quantity
                + quantity
            )
        )

        if final_quantity > variant.stock:
            available_to_add = max(
                variant.stock
                - (
                    0
                    if created
                    else cart_item.quantity
                ),
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
                    "available_stock":
                        variant.stock,
                },
                status=
                    status.HTTP_400_BAD_REQUEST,
            )

        if (
            final_quantity
            > MAX_CART_ITEM_QUANTITY
        ):
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
                status=
                    status.HTTP_400_BAD_REQUEST,
            )

        if not created:
            cart_item.quantity = (
                final_quantity
            )

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
class UpdateCartItemView(
    generics.GenericAPIView
):
    """
    تغییر تعداد یک آیتم سبد خرید.
    """

    serializer_class = (
        CartItemUpdateSerializer
    )

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
        input_serializer = (
            self.get_serializer(
                data=request.data,
            )
        )

        input_serializer.is_valid(
            raise_exception=True,
        )

        quantity = (
            input_serializer
            .validated_data["quantity"]
        )

        if quantity > MAX_CART_ITEM_QUANTITY:
            return Response(
                {
                    "error": (
                        f"حداکثر تعداد مجاز "
                        f"{MAX_CART_ITEM_QUANTITY} "
                        "عدد است."
                    ),
                },
                status=
                    status.HTTP_400_BAD_REQUEST,
            )

        cart = get_user_cart(request)

        cart_item = get_object_or_404(
            CartItem.objects
            .select_related(
                "variant",
                "variant__product",
            ),
            id=pk,
            cart=cart,
        )

        if (
            quantity
            > cart_item.variant.stock
        ):
            return Response(
                {
                    "error": (
                        f"فقط "
                        f"{cart_item.variant.stock} "
                        "عدد موجود است."
                    ),
                    "available_stock":
                        cart_item.variant.stock,
                },
                status=
                    status.HTTP_400_BAD_REQUEST,
            )

        cart_item.quantity = quantity

        cart_item.save(
            update_fields=["quantity"],
        )

        return Response(
            {
                "message":
                    "تعداد آیتم بروزرسانی شد.",
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
class RemoveCartItemView(
    generics.GenericAPIView
):
    """
    حذف یک آیتم از سبد خرید.
    """

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
                "message":
                    "آیتم از سبد خرید حذف شد.",
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
    """
    حذف تمام آیتم‌های سبد خرید.
    """

    permission_classes = [AllowAny]

    def delete(self, request):
        cart = get_user_cart(request)
        cart.items.all().delete()

        return Response(
            {
                "message": (
                    "سبد خرید با موفقیت "
                    "خالی شد."
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
    """
    ثبت نهایی سفارش از سبد خرید کاربر.

    ورودی مورد انتظار:

    {
        "address_id": 1,
        "shipping_quote_id": "uuid",
        "shipping_method_code":
            "fixed_standard",
        "payment_method": "online"
    }

    نکات امنیتی:

    - مبلغ کالاها از فرانت دریافت نمی‌شود.
    - هزینه ارسال از فرانت دریافت نمی‌شود.
    - موجودی در transaction و با select_for_update
      بررسی می‌شود.
    - آدرس فقط در صورتی پذیرفته می‌شود که متعلق به
      مشتری فعلی باشد.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = CreateOrderSerializer

    @transaction.atomic
    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        # ---------------------------------------------
        # ۱. اعتبارسنجی داده ورودی
        # ---------------------------------------------
        input_serializer = (
            self.get_serializer(
                data=request.data,
            )
        )

        input_serializer.is_valid(
            raise_exception=True,
        )

        validated_data = (
            input_serializer.validated_data
        )

        address_id = validated_data[
            "address_id"
        ]

        shipping_quote_id = validated_data[
            "shipping_quote_id"
        ]

        shipping_method_code = (
            validated_data[
                "shipping_method_code"
            ]
        )

        payment_method = validated_data[
            "payment_method"
        ]

        # ---------------------------------------------
        # ۲. دریافت پروفایل مشتری
        # ---------------------------------------------
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
                status=
                    status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # ۳. بررسی مالکیت آدرس
        # ---------------------------------------------
        address = get_object_or_404(
            CustomerAddress,
            id=address_id,
            customer=customer,
        )

        # ---------------------------------------------
        # ۴. دریافت و قفل‌کردن سبد خرید
        # ---------------------------------------------
        cart = get_user_cart(request)

        cart = (
            Cart.objects
            .select_for_update()
            .get(pk=cart.pk)
        )

        cart_items = list(
            cart.items
            .select_related(
                "variant",
                "variant__product",
            )
        )

        if not cart_items:
            return Response(
                {
                    "error":
                        "سبد خرید خالی است.",
                },
                status=
                    status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # ۵. قفل‌کردن واریانت‌ها
        # ---------------------------------------------
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

        # ---------------------------------------------
        # ۶. بررسی موجودی و محاسبه مبلغ کالاها
        # ---------------------------------------------
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
                    status=(
                        status
                        .HTTP_400_BAD_REQUEST
                    ),
                )

            if (
                variant.stock
                < cart_item.quantity
            ):
                return Response(
                    {
                        "error": (
                            f"محصول "
                            f"{variant.product.name} "
                            f"فقط {variant.stock} "
                            "عدد موجودی دارد."
                        ),
                        "variant_id":
                            variant.id,
                        "available_stock":
                            variant.stock,
                    },
                    status=(
                        status
                        .HTTP_400_BAD_REQUEST
                    ),
                )

            unit_price = (
                get_variant_unit_price(
                    variant
                )
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

        # ---------------------------------------------
        # ۷. محاسبه مجدد هزینه ارسال در بک‌اند
        # ---------------------------------------------
        shipping_quote = (
            FixedShippingQuoteService(
                cart=cart,
                address=address,
            ).calculate()
        )

        available_methods = (
            shipping_quote.get(
                "methods",
                [],
            )
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
                status=
                    status.HTTP_400_BAD_REQUEST,
            )

        shipping_cost = decimal_from_value(
            selected_method.get(
                "cost",
                0,
            )
        )

        shipping_method_title = str(
            selected_method.get(
                "title",
                "",
            )
        ).strip()

        # ---------------------------------------------
        # ۸. ساخت Snapshot آدرس
        # ---------------------------------------------
        address_snapshot = (
            build_address_snapshot(
                address
            )
        )

        # ---------------------------------------------
        # ۹. ساخت سفارش
        # ---------------------------------------------
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

            payment_method=(
                payment_method
            ),

            items_total=items_total,

            shipping_cost=(
                shipping_cost
            ),

            discount_amount=(
                Decimal("0")
            ),
        )

        # ---------------------------------------------
        # ۱۰. ساخت آیتم‌های سفارش
        # ---------------------------------------------
        order_items = [
            OrderItem(
                order=order,
                variant=data["variant"],
                quantity=data["quantity"],
                price=data["price"],
            )
            for data in order_items_data
        ]

        OrderItem.objects.bulk_create(
            order_items
        )

        # ---------------------------------------------
        # ۱۱. کم‌کردن موجودی
        # ---------------------------------------------
        for data in order_items_data:
            variant = data["variant"]

            variant.stock -= (
                data["quantity"]
            )

            variant.save(
                update_fields=["stock"],
            )

        # ---------------------------------------------
        # ۱۲. خالی‌کردن سبد
        # ---------------------------------------------
        cart.items.all().delete()

        # ---------------------------------------------
        # ۱۳. پاسخ نهایی
        # ---------------------------------------------
        output_serializer = (
            OrderSerializer(
                order,
                context={
                    "request": request,
                },
            )
        )

        return Response(
            {
                "message":
                    "سفارش با موفقیت ثبت شد.",
                "order":
                    output_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


# =========================================================
# لیست سفارش‌های کاربر
# =========================================================
class OrderListView(
    generics.ListAPIView
):
    """
    نمایش تمام سفارش‌های کاربر واردشده.
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects
            .filter(
                user=self.request.user
            )
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
    """
    نمایش جزئیات یک سفارش متعلق به کاربر.
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects
            .filter(
                user=self.request.user
            )
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
    """
    لغو سفارش در وضعیت pending و بازگرداندن موجودی.
    """

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
                status=
                    status.HTTP_400_BAD_REQUEST,
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

        order.status = (
            Order.STATUS_CANCELLED
        )

        order.save(
            update_fields=["status"],
        )

        return Response(
            {
                "message":
                    "سفارش با موفقیت لغو شد.",

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
# ادغام سبد مهمان با سبد کاربر
# =========================================================
class MergeCartView(APIView):
    """
    ادغام سبد خرید مهمان با حساب کاربری.

    Endpoint:

    POST /api/orders/cart/merge/

    Body:

    {
        "session_key": "abc123"
    }
    """

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
                status=
                    status.HTTP_400_BAD_REQUEST,
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
