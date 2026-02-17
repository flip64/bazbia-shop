from django.urls import path
from orders.api import views

app_name = 'orders'  # اضافه کردن namespace

urlpatterns = [
    # محصولات ویژه
    path('weekly-best-sellers/', views.WeeklyBestSellersAPIView.as_view(), name='weekly-best-sellers'),
    path('special-offers/', views.SpecialOffersView.as_view(), name='special-offers'),
#    path('flash-sales/', views.FlashSalesView.as_view(), name='flash-sales'),
    
    # سبد خرید
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/', views.AddToCartView.as_view(), name='add-to-cart'),
    path('cart/item/<int:pk>/update/', views.UpdateCartItemView.as_view(), name='update-cart-item'),
    path('cart/item/<int:pk>/delete/', views.RemoveCartItemView.as_view(), name='remove-cart-item'),
    path('cart/clear/', views.ClearCartView.as_view(), name='clear-cart'),
    path('cart/save/', views.SaveCartView.as_view(), name='save-cart'),
    path('cart/load/', views.LoadSavedCartView.as_view(), name='load-cart'),
    
    # سفارشات
    path('orders/create/', views.CreateOrderView.as_view(), name='create-order'),
    path('orders/', views.OrderListView.as_view(), name='order-list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:pk>/cancel/', views.CancelOrderView.as_view(), name='cancel-order'),
    path('orders/track/<str:tracking_code>/', views.TrackOrderView.as_view(), name='track-order'),
    path('orders/returns/', views.ReturnRequestView.as_view(), name='return-request'),
]
