# orders/api/views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Case, When, IntegerField
from products.models import Product,ProductVariant
from products.api.serializers import ProductListSerializer
from products.api.pagination import CustomCategoryPagination
from orders.utils.cart import CartManager
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db import transaction
from orders.models import Cart, CartItem, Order, OrderItem,SalesSummary
from orders.api.serializers import (
    CartSerializer,
    CartItemSerializer,
    CartItemInputSerializer,
    OrderSerializer
)







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

        for p in products:
            if timezone.is_aware(p.created_at):
                p.created_at = timezone.localtime(p.created_at)

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
                "count": queryset.count(),
                "data": serializer.data
            })

        except Exception as e:
            return Response({
                "success": False,
                "message": "خطا در دریافت اطلاعات",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ==============================
# 🎯 Helper Function
# ==============================
def get_user_cart(request):
    """دریافت یا ایجاد سبد خرید برای کاربر یا سشن مهمان"""
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key or request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=session_key)
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
# ➕ 2. افزودن آیتم به سبد خرید
# ==============================
class AddToCartView(generics.GenericAPIView):
    serializer_class = CartItemInputSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        variant_id = serializer.validated_data['variant_id']
        quantity = serializer.validated_data['quantity']

        cart = get_user_cart(request)
        variant = get_object_or_404(ProductVariant, id=variant_id)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            variant=variant,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return Response({
            "message": "آیتم با موفقیت به سبد خرید افزوده شد.",
            "item": CartItemSerializer(cart_item, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)


# ==============================
# ✏️ 3. بروزرسانی آیتم سبد خرید
# ==============================
class UpdateCartItemView(generics.GenericAPIView):
    serializer_class = CartItemInputSerializer
    permission_classes = [AllowAny]

    def put(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quantity = serializer.validated_data['quantity']

        cart = get_user_cart(request)
        cart_item = get_object_or_404(CartItem, id=pk, cart=cart)

        cart_item.quantity = quantity
        cart_item.save()

        return Response({
            "message": "تعداد آیتم بروزرسانی شد.",
            "item": CartItemSerializer(cart_item, context={'request': request}).data
        })


# ==============================
# ❌ 4. حذف آیتم از سبد خرید
# ==============================
class RemoveCartItemView(generics.DestroyAPIView):
    permission_classes = [AllowAny]

    def delete(self, request, pk):
        cart = get_user_cart(request)
        cart_item = get_object_or_404(CartItem, id=pk, cart=cart)
        cart_item.delete()
        return Response({"message": "آیتم از سبد خرید حذف شد."}, status=status.HTTP_204_NO_CONTENT)


# ==============================
# 🧹 5. خالی کردن کل سبد خرید
# ==============================
class ClearCartView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def delete(self, request):
        cart = get_user_cart(request)
        cart.items.all().delete()
        return Response({"message": "سبد خرید با موفقیت خالی شد."})


# ==============================
# 🧾 6. ایجاد سفارش از سبد خرید
# ==============================
class CreateOrderView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        cart = get_user_cart(request)
        if not cart.items.exists():
            return Response({"error": "سبد خرید خالی است."}, status=status.HTTP_400_BAD_REQUEST)

        # ایجاد سفارش
        order = Order.objects.create(user=request.user, status='pending')

        # انتقال آیتم‌ها از سبد به سفارش
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                variant=item.variant,
                quantity=item.quantity,
                price=item.variant.discount_price or item.variant.price
            )

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
# 🚫 9. لغو سفارش (در حالت pending)
# ==============================
class CancelOrderView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        order = get_object_or_404(Order, id=pk, user=request.user)
        if order.status != 'pending':
            return Response({"error": "این سفارش دیگر قابل لغو نیست."}, status=status.HTTP_400_BAD_REQUEST)

        order.status = 'cancelled'
        order.save()

        return Response({
            "message": "سفارش لغو شد.",
            "order": OrderSerializer(order, context={'request': request}).data
        })
