from django.urls import path
from . import views

urlpatterns = [
    path('user-cart/', views.select_user_cart, name='select_user_cart'),

]





