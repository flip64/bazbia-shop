from django.urls import path
from . import category_api
from products.api import views


urlpatterns = [
    path('', views.ProductListAPIView.as_view(), name='product-list'),

    # مسیرهای خاص باید قبل از slug باشند
    path('categories/', views.CategoryListAPIView.as_view(), name='category-list'),
    path('categories/<slug:slug>/', views.ProductListCategoryAPIView.as_view(), name='list_categories_api'),
    path('import-categories/', category_api.import_categories, name='import-categories'),
    path('specialproduct/', views.SpecialProductListAPIView.as_view(), name='specialproduct'),
    path('new_products/', views.NewProductsAPIView.as_view(), name='newproducts'),
    
    
    # در آخر مسیر slug رو بذار
    path('<slug:slug>/', views.ProductDetailAPIView.as_view(), name='product-detail'),
]
