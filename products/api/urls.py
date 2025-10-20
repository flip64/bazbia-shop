from django.urls import path
from . import category_api
from products.api import views

urlpatterns = [
    # لیست محصولات ساده با فیلتر دسته
    path('', views.ProductListAPIView.as_view(), name='product-list'),

    # لیست کامل محصولات با جزئیات
    path('full-products/', views.ProductFullListAPIView.as_view(), name='product-full-list'),




    
    # مسیرهای دسته‌بندی
    path('categories/', views.CategoryListAPIView.as_view(), name='category-list'),
    path('categories/<slug:slug>/', views.ProductListCategoryAPIView.as_view(), name='list_categories_api'),
    path('import-categories/', category_api.import_categories, name='import-categories'),

    # محصولات ویژه و جدید
    path('specialproduct/', views.SpecialProductListAPIView.as_view(), name='specialproduct'),
    path('new_products/', views.NewProductsAPIView.as_view(), name='newproducts'),

    # جزئیات محصول بر اساس slug
    path('<slug:slug>/', views.ProductDetailAPIView.as_view(), name='product-detail'),
]
