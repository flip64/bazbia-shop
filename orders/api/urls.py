from django.urls import path
from orders.api.views import WeeklyBestSellersAPIView , CartView

urlpatterns = [
    path("weeklyBestSellers/", WeeklyBestSellersAPIView.as_view(), name="weekly-best-sellers"),
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/', views.AddToCartView.as_view(), name='add_to_cart'),
    path('cart/item/<int:pk>/update/', views.UpdateCartItemView.as_view(), name='update_cart_item'),
    path('cart/item/<int:pk>/delete/', views.RemoveCartItemView.as_view(), name='remove_cart_item'),
    path('cart/clear/', views.ClearCartView.as_view(), name='clear_cart'),
    path('orders/create/', views.CreateOrderView.as_view(), name='create_order'),
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/cancel/', views.CancelOrderView.as_view(), name='cancel_order'),
    
]

