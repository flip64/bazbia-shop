from django.urls import path
from scrap_abdisite import views 
app_name = 'scrap_abdisite'


urlpatterns = [

    #path('', views.product_price_list, name='product_price_list'),
        # لیست همه لینک‌ها + قیمت تأمین‌کننده + فرم قیمت فروش
    path("watched_urls/", views.product_price_list, name="product_price_list"),

    # بروزرسانی قیمت فروش و تخفیف یک واریانت
    path("watched_urls/<int:pk>/update/", views.watched_urls_update, name="watched_urls_update"),

    
    
    
    
    path('delet/<int:id>/', views.delet, name='delet'),
    path('create_product/', views.create_product , name= 'create_product'),
    path('fetch_details_products/',views.fetch_details_products , name= 'fetch_details_products'),
    
    

]
