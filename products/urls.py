from django.urls import path
from . import views

app_name = 'products'  # برای namespace مهمه

urlpatterns = [
    path('', views.product_list, name='product_list'),  # /products/
    path('<slug:slug>/', views.product_detail, name='product_detail'),  # /products/some-product/
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),  # /products/category/slug/
    path('categories/', views.category_list, name='category_list'),  # /products/categories/
    path('category/create/', views.category_create, name='category_create'),  # /products/category/create/
    path('category/<int:pk>/edit/', views.category_edit, name='category_edit'),  # /products/category/1/edit/
]
