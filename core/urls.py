# products/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('login', views.login, name='login'),
    path('<slug:slug>/', views.product_detail, name='product_detail'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),

]
