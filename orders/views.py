from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from .models import Cart

User = get_user_model()

def view_user_cart(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    # سعی می‌کنیم آخرین سبد خرید کاربر را بگیریم
    cart = Cart.objects.filter(user=user).order_by('-updated_at').first()
    
    if cart:
        cart_items = cart.items.all()
        total = sum(item.total_price() for item in cart_items)
    else:
        cart_items = []
        total = 0

    context = {
        'user': user,
        'cart': cart,
        'cart_items': cart_items,
        'total': total
    }
    return render(request, 'view_cart.html', context)
