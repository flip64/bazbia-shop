from django.urls import path
from scrap_abdisite import views 
app_name = 'scrap_abdisite'


urlpatterns = [

    path('', views.watched_urls_view, name='watched_urls'),
    path('watched_urls/', views.watched_urls_view, name='watched_urls'),
    path('delet/<int:id>/', views.delet, name='delet'),
    path('checkall/', views.check_price_all,name='check_price_all'),
    path('create_product/', views.create_product , name= 'create_product'),
    path('change_price_all/',views.change_price_all , name= 'change_price_all'),
    path('fetch_details_products/',views.fetch_details_products , name= 'fetch_details_products'),
    
    

]
