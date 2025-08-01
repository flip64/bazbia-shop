from django.urls import path
from products import views

app_name = 'products'  # برای namespace مهمه

urlpatterns = [
    path('', views.product_list, name='root_product'),  # /products/
    path('category/', views.category_detail, name='category_detail'),  # /products/category/slug/
    path('categories/', views.category_list, name='category_list'),  # /products/categories/
    path('category/create/', views.category_create, name='category_create'),  # /products/category/create/
    path('category/<int:pk>/edit/', views.category_edit, name='category_edit'),  # /products/category/1/edit/
   
    
    path('product_detail/<slug:slug>/', views.product_detail, name='product_detail'),
]
