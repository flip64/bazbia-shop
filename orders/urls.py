from django.urls import path
from . import views

urlpatterns = [
    path('cart/<int:user_id>/', views.view_user_cart, name='view_user_cart'),
]
