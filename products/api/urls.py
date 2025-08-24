from django.urls import path
from . import category_api
from django.urls import path
from products.api import views
from products.api.views import NewProductsAPIView

    
urlpatterns = [
    path('categories/', category_api.list_categories, name='list_categories_api'),
    path('import-categories/', category_api.import_categories, name='import-categories'),
    path('products/', views.ProductListAPIView.as_view(), name='product-list'),
    path('products/<slug:slug>/', views.ProductDetailAPIView.as_view(), name='product-detail'),
    path('products/categories/', views.CategoryListAPIView.as_view(), name='category-list'),
    path('specialproduct/', views.SpecialProductListAPIView.as_view(), name='specialproduct'),
    path('new_products/', NewProductsAPIView.as_view(), name='newproducts'),


]










