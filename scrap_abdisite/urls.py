from django.urls import path
from scrap_abdisite.views  import views
from scrap_abdisite.views.price_history_view import price_history_view
from scrap_abdisite.views import watched_urls_update
app_name = "scrap_abdisite"

urlpatterns = [
    # 🔹 مدیریت لینک‌های پایش شده
    path('watched_urls/', views.product_price_list, name='product_price_list'),
    path('watched_urls/<int:watched_id>/update/', watched_urls_update, name='watched_urls_update'),
    path('watched_urls/<int:watched_id>/delete/', views.delete_watched_url, name='watched_urls_delete'),
  
    path("toggle-product/<int:product_id>/", views.toggle_product_status, name="toggle_product_status"),
    # 🔹 پردازش پس‌زمینه
    path('fetch_details_products/', views.fetch_details_products, name='fetch_details_products'),

    # 🔹 ایمپورت محصول
    path('create_product/', views.create_product, name='create_product'),

    # 🔹 تصاویر محصول
    path('product/<slug:slug>/images/', views.product_images_by_slug, name='product_images_by_slug'),
    path('product/<slug:slug>/images/<int:image_id>/update/', views.product_image_update_by_slug, name='product_image_update_by_slug'),

    # 🔹 تغییرات قیمت
    path('watched_urls/<int:watched_id>/history/', price_history_view, name='watched_urls_history'),
]
