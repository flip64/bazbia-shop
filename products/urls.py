# products/urls.py
from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('home', views.home, name='home'),
    path('<slug:slug>/', views.product_detail, name='product_detail'),
  #  path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/new/', views.category_create, name='category_create'),
    path('categories/edit/<int:pk>/', views.category_edit, name='category_edit'),
]





urlpatterns = [
    
]
