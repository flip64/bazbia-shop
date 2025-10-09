from django.urls import path
from scrap_abdisite import views 
app_name = 'scrap_abdisite'


from django.urls import path
from . import views

app_name = 'scrap_abdisite'




urlpatterns = [

    #path('', views.product_price_list, name='product_price_list'),
        # لیست همه لینک‌ها + قیمت تأمین‌کننده + فرم قیمت فروش
    path("watched_urls/", views.product_price_list, name="product_price_list"),

    # بروزرسانی قیمت فروش و تخفیف یک واریانت
    path("watched_urls/<int:watched_id>/update/", views.watched_urls_update, name="watched_urls_update"),

    
    path('watched_urls/<int:watched_id>/delete/', views.delet, name='watched_urls_delete'),
    
    path('create_product/', views.create_product , name= 'create_product'),
    path('fetch_details_products/',views.fetch_details_products , name= 'fetch_details_products'),

    
    # مشاهده همه تصاویر یک محصول با slug
    path('product/<slug:slug>/images/', 
         views.product_images_by_slug, 
         name='product_images_by_slug'),

    # آپدیت یک تصویر محصول
    path('product/<slug:slug>/images/<int:image_id>/update/', 
         views.product_image_update_by_slug, 
         name='product_image_update_by_slug'),

]





 








