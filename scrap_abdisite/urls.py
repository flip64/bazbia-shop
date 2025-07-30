from django.urls import path
from scrap_abdisite import views 
app_name = 'scrap_abdisite'


urlpatterns = [

    path('', views.watched_urls_view, name='watched_urls'),
    path('check_price/', views.check_price, name='check_price'),
    path('watched_urls/', views.watched_urls_view, name='watched_urls'),
    path('delet/<int:id>/', views.delet, name='delet'),
    path('checkall/', views.check_price_all,name='check_price_all'),
    path('create_product/', views.create_product , name= 'create_product'),
    

]