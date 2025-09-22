from django.conf import settings
from orders.models import Cart, CartItem
from products.models import ProductVariant

class CartManager:
    def __init__(self, request):
        self.request = request
        self.user = request.user if request.user.is_authenticated else None

        # اگر session_key نداریم، بسازیم
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.save()
            session_key = self.request.session.session_key
        self.session_key = session_key

        # گرفتن یا ساخت سبد
        self.cart = self.get_or_create_cart()

    def get_or_create_cart(self):
        if self.user:
            cart, created = Cart.objects.get_or_create(user=self.user)
        else:
            cart, created = Cart.objects.get_or_create(session_key=self.session_key, user__isnull=True)
        return cart

    def add(self, variant_id, quantity=1):
        variant = ProductVariant.objects.get(id=variant_id)
        item, created = CartItem.objects.get_or_create(cart=self.cart, variant=variant)
        if not created:
            item.quantity += quantity
        else:
            item.quantity = quantity
        item.save()

    def remove(self, variant_id):
        CartItem.objects.filter(cart=self.cart, variant_id=variant_id).delete()

    def update(self, variant_id, quantity):
        try:
            item = CartItem.objects.get(cart=self.cart, variant_id=variant_id)
            item.quantity = quantity
            if quantity <= 0:
                item.delete()
            else:
                item.save()
        except CartItem.DoesNotExist:
            pass

    def clear(self):
        self.cart.items.all().delete()

    def items(self):
        return self.cart.items.select_related('variant')

    def total_price(self):
        return self.cart.total_price()

    def merge_session_cart(self, session_cart_data):
        """
        ادغام داده‌های سبد session (دیکشنری) با سبد دیتابیس
        session_cart_data: dict مانند {'variant_id': {'quantity': x}, ...}
        """
        for variant_id_str, data in session_cart_data.items():
            variant_id = int(variant_id_str)
            quantity = data.get('quantity', 0)
            if quantity <= 0:
                continue
            try:
                variant = ProductVariant.objects.get(id=variant_id)
            except ProductVariant.DoesNotExist:
                continue

            item, created = CartItem.objects.get_or_create(cart=self.cart, variant=variant)
            if not created:
                item.quantity += quantity
            else:
                item.quantity = quantity
            item.save()
