# orders/api/views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Case, When, IntegerField
from products.models import Product, ProductVariant
from products.api.serializers import ProductListSerializer
from products.api.pagination import CustomCategoryPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db import transaction
from orders.models import Cart, CartItem, Order, OrderItem, SalesSummary
from orders.api.serializers import (
    CartSerializer,
    CartItemSerializer,
    CartItemInputSerializer,
    OrderSerializer
)

# ===========================
# SpecialOffersView
# ===========================
class SpecialOffersView(APIView):
    """
    دریافت محصولات با تخفیف ویژه
    """
    def get(self, request):
        products = Product.objects.filter(
            discount_price__isnull=False,
            is_special=True
        )[:10]  # ۱۰ محصول برتر
        serializer = ProductSerializer(products, many=True)
        return Response({
            'count': products.count(),
            'results': serializer.data
        })
        



# ===========================
# Weekly Best Sellers API
# ===========================
class WeeklyBestSellersAPIView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    pagination_class = CustomCategoryPagination

    def get_queryset(self):
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)

        sales_qs = (
            SalesSummary.objects
            .filter(created_at__date__range=(week_ago, today))
            .values("product_id")
            .annotate(total_sold=Sum("total_quantity"))
            .order_by("-total_sold")
        )

        product_ids = [s["product_id"] for s in sales_qs]

        if product_ids:
            preserved_order = Case(
                *[When(id=pid, then=pos) for pos, pid in enumerate(product_ids)],
                output_field=IntegerField()
            )
            products = Product.objects.filter(id__in=product_ids).order_by(preserved_order)
        else:
            products = Product.objects.filter(is_active=True).order_by("-created_at")

        return products

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.get_serializer(page, many=True, context={'request': request})
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True, context={'request': request})
            return Response({
                "success": True,
                "data": serializer.data,
                "count": queryset.count()
            })

        except Exception as e:
            return Response({
                "success": False,
                "message": "خطا در دریافت اطلاعات",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==============================
# 🎯 Helper Function - اصلاح شده
# ==============================
def get_user_cart(request):
    """
    دریافت یا ایجاد سبد خرید برای کاربر یا مهمان
    - کاربر لاگین کرده: یک سبد خرید دارد (با فرض OneToOneField)
    - کاربر مهمان: بر اساس session_key
    """
    if request.user.is_authenticated:
        # کاربر لاگین کرده - با فرض OneToOneField
        cart, created = Cart.objects.get_or_create(
            user=request.user,
            defaults={'session_key': None}
        )
        
        # اگر سبد خرید قبلی با session_key داشته، پاکش می‌کنیم
        if not created and cart.session_key:
            cart.session_key = None
            cart.save()
            
        return cart
    
    else:
        # کاربر مهمان
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        cart, created = Cart.objects.get_or_create(
            session_key=session_key,
            defaults={'user': None}
        )
        
        return cart


# ==============================
# 🛒 1. مشاهده سبد خرید
# ==============================
class CartView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        return get_user_cart(self.request)


# ==============================
# ➕ 2. افزودن آیتم به سبد خرید - اصلاح شده
# ==============================
class AddToCartView(generics.GenericAPIView):
    serializer_class = CartItemInputSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        variant_id = serializer.validated_data['variant_id']
        quantity = serializer.validated_data['quantity']

        # اعتبارسنجی تعداد
        if quantity <= 0:
            return Response({
                "error": "تعداد باید بیشتر از صفر باشد"
            }, status=status.HTTP_400_BAD_REQUEST)

        cart = get_user_cart(request)
        variant = get_object_or_404(ProductVariant, id=variant_id)

        # بررسی موجودی
        if variant.stock < quantity:
            return Response({
                "error": f"فقط {variant.stock} عدد موجود است."
            }, status=status.HTTP_400_BAD_REQUEST)

        # بررسی حداکثر تعداد مجاز (اختیاری)
        MAX_QUANTITY = 10
        if quantity > MAX_QUANTITY:
            return Response({
                "error": f"حداکثر تعداد مجاز {MAX_QUANTITY} عدد است."
            }, status=status.HTTP_400_BAD_REQUEST)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            variant=variant,
            defaults={'quantity': quantity}
        )

        if not created:
            # بررسی مجموع تعداد با موجودی
            total_quantity = cart_item.quantity + quantity
            if variant.stock < total_quantity:
                return Response({
                    "error": f"موجودی کافی نیست. حداکثر می‌توانید {variant.stock - cart_item.quantity} عدد دیگر اضافه کنید."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if total_quantity > MAX_QUANTITY:
                return Response({
                    "error": f"حداکثر تعداد مجاز {MAX_QUANTITY} عدد است."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            cart_item.quantity = total_quantity
            cart_item.save()

        return Response({
            "message": "آیتم با موفقیت به سبد خرید افزوده شد.",
            "item": CartItemSerializer(cart_item, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)


# ==============================
# ✏️ 3. بروزرسانی آیتم سبد خرید - اصلاح شده
# ==============================
class UpdateCartItemView(generics.GenericAPIView):
    serializer_class = CartItemInputSerializer
    permission_classes = [AllowAny]

    def put(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        quantity = serializer.validated_data['quantity']

        # اعتبارسنجی تعداد
        if quantity <= 0:
            return Response({
                "error": "تعداد باید بیشتر از صفر باشد"
            }, status=status.HTTP_400_BAD_REQUEST)

        cart = get_user_cart(request)
        cart_item = get_object_or_404(CartItem, id=pk, cart=cart)

        # بررسی موجودی
        if cart_item.variant.stock < quantity:
            return Response({
                "error": f"فقط {cart_item.variant.stock} عدد موجود است."
            }, status=status.HTTP_400_BAD_REQUEST)

        # بررسی حداکثر تعداد
        MAX_QUANTITY = 10
        if quantity > MAX_QUANTITY:
            return Response({
                "error": f"حداکثر تعداد مجاز {MAX_QUANTITY} عدد است."
            }, status=status.HTTP_400_BAD_REQUEST)

        cart_item.quantity = quantity
        cart_item.save()

        return Response({
            "message": "تعداد آیتم بروزرسانی شد.",
            "item": CartItemSerializer(cart_item, context={'request': request}).data
        })


# ==============================
# ❌ 4. حذف آیتم از سبد خرید
# ==============================
class RemoveCartItemView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def delete(self, request, pk):
        cart = get_user_cart(request)
        cart_item = get_object_or_404(CartItem, id=pk, cart=cart)
        cart_item.delete()
        
        return Response({
            "message": "آیتم از سبد خرید حذف شد."
        }, status=status.HTTP_200_OK)  # 204 No Content به خاطر فرانت بعضی وقتا مشکل داره


# ==============================
# 🧹 5. خالی کردن کل سبد خرید
# ==============================
class ClearCartView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def delete(self, request):
        cart = get_user_cart(request)
        cart.items.all().delete()
        
        return Response({
            "message": "سبد خرید با موفقیت خالی شد."
        })


# ==============================
# 🧾 6. ایجاد سفارش از سبد خرید - اصلاح شده
# ==============================
class CreateOrderView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        cart = get_user_cart(request)
        
        # بررسی خالی نبودن سبد
        if not cart.items.exists():
            return Response({
                "error": "سبد خرید خالی است."
            }, status=status.HTTP_400_BAD_REQUEST)

        # محاسبه مبلغ کل
        total_price = cart.total_price()

        # بررسی موجودی همه آیتم‌ها یکجا
        for item in cart.items.all():
            if item.variant.stock < item.quantity:
                return Response({
                    "error": f"محصول {item.variant.product.name} تنها {item.variant.stock} عدد موجود است."
                }, status=status.HTTP_400_BAD_REQUEST)

        # ایجاد سفارش - توجه: مدل Order باید فیلد total_price داشته باشد
        order = Order.objects.create(
            user=request.user,
            total_price=total_price,  # مطمئن شوید این فیلد در مدل هست
            status='pending'
        )

        # انتقال آیتم‌ها از سبد به سفارش و کاهش موجودی
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                variant=item.variant,
                quantity=item.quantity,
                price=item.price()  # قیمت لحظه ثبت سفارش
            )
            
            # کاهش موجودی
            item.variant.stock -= item.quantity
            item.variant.save()

        # خالی کردن سبد
        cart.items.all().delete()

        return Response({
            "message": "سفارش با موفقیت ثبت شد.",
            "order": OrderSerializer(order, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)


# ==============================
# 📋 7. مشاهده لیست سفارش‌های کاربر
# ==============================
class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


# ==============================
# 🔍 8. مشاهده جزئیات سفارش خاص
# ==============================
class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


# ==============================
# 🚫 9. لغو سفارش (در حالت pending) - اصلاح شده
# ==============================
class CancelOrderView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        order = get_object_or_404(Order, id=pk, user=request.user)
        
        # فقط سفارش‌های در انتظار قابل لغو هستند
        if order.status != 'pending':
            return Response({
                "error": "این سفارش دیگر قابل لغو نیست."
            }, status=status.HTTP_400_BAD_REQUEST)

        # برگردوندن موجودی به انبار
        for item in order.items.all():
            item.variant.stock += item.quantity
            item.variant.save()

        # تغییر وضعیت سفارش
        order.status = 'cancelled'
        order.save()

        return Response({
            "message": "سفارش با موفقیت لغو شد.",
            "order": OrderSerializer(order, context={'request': request}).data
        })
