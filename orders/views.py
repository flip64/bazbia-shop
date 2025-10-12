from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from .models import Cart

User = get_user_model()

def select_user_cart(request):
    users = User.objects.all()
    selected_user = None
    cart_items = []
    total = 0

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        if user_id:
            selected_user = get_object_or_404(User, id=user_id)
            cart = Cart.objects.filter(user=selected_user).order_by('-updated_at').first()
            if cart:
                cart_items = cart.items.all()
                total = sum(item.total_price() for item in cart_items)

    context = {
        'users': users,
        'selected_user': selected_user,
        'cart_items': cart_items,
        'total': total
    }
    return render(request, 'select_user_cart.html', context)
