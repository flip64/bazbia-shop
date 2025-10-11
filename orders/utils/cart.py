from datetime import timedelta
from django.utils import timezone
from orders.models import Cart, CartItem
from products.models import ProductVariant

class CartManager:
    def __init__(self, request):
        self.request = request
        self.user = request.user if request.user.is_authenticated else None
        self.session_key = self.get_session_key()
        self.cart = self.get_or_create_cart()

    def get_session_key(self):
        if not self.request.session.session_key:
            self.request.session.save()
        return self.request.session.session_key

    def get_or_create_cart(self):
        if self.user:
            cart, _ = Cart.objects.get_or_create(user=self.user)
        else:
            cart, _ = Cart.objects.get_or_create(
                session_key=self.session_key,
                user__isnull=True
            )
        return cart

    def add(self, variant_id, quantity=1):
        variant = ProductVariant.objects.get(id=variant_id)

        # محدودیت موجودی
        if quantity > variant.stock:
            quantity = variant.stock

        item, created = CartItem.objects.get_or_create(cart=self.cart, variant=variant)
        if not created:
            new_qty = item.quantity + quantity
            if new_qty > variant.stock:
                new_qty = variant.stock
            item.quantity = new_qty
        else:
            item.quantity = quantity

        item.save()
        return item

    def update(self, variant_id, quantity):
        try:
            item = CartItem.objects.get(cart=self.cart, variant_id=variant_id)
            if quantity <= 0:
                item.delete()
            else:
                if quantity > item.variant.stock:
                    quantity = item.variant.stock
                item.quantity = quantity
                item.save()
        except CartItem.DoesNotExist:
            pass

    def remove(self, variant_id):
        CartItem.objects.filter(cart=self.cart, variant_id=variant_id).delete()

    def clear(self):
        self.cart.items.all().delete()

    def items(self):
        return self.cart.items.select_related("variant", "variant__product")

    def total_price(self):
        return sum(
            (item.variant.discount_price or item.variant.price) * item.quantity
            for item in self.cart.items.all()
        )

    def merge_session_cart(self, session_cart_data):
        """
        ادغام سبد session با سبد کاربر لاگین‌شده
        session_cart_data: dict {variant_id: {"quantity": x}}
        """
        for variant_id_str, data in session_cart_data.items():
            variant_id = int(variant_id_str)
            quantity = data.get("quantity", 0)
            if quantity <= 0:
                continue

            try:
                variant = ProductVariant.objects.get(id=variant_id)
            except ProductVariant.DoesNotExist:
                continue

            item, created = CartItem.objects.get_or_create(cart=self.cart, variant=variant)
            if not created:
                new_qty = item.quantity + quantity
                if new_qty > variant.stock:
                    new_qty = variant.stock
                item.quantity = new_qty
            else:
                if quantity > variant.stock:
                    quantity = variant.stock
                item.quantity = quantity
            item.save()
