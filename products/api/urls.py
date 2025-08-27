from django.urls import path
from . import category_api
from django.urls import path
from products.api import views
from products.api.views import NewProductsAPIView

    
urlpatterns = [
    path('', views.ProductListAPIView.as_view(), name='product-list'),
    path('<slug:slug>/', views.ProductDetailAPIView.as_view(), name='product-detail'),
    path('categories/', views.CategoryListAPIView.as_view(), name='category-list'),
    path('categories/<slug:slug>/', views.ProductListCategoryAPIView.as_view, name='list_categories_api'), #   محصولات یک دسته خاص را برمی گرداند    
    path('import-categories/', category_api.import_categories, name='import-categories'),
    
         
    path('specialproduct/', views.SpecialProductListAPIView.as_view(), name='specialproduct'),
    path('new_products/', NewProductsAPIView.as_view(), name='newproducts'),


]








