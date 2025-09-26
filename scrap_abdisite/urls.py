from django.urls import path
from scrap_abdisite import views 
app_name = 'scrap_abdisite'


urlpatterns = [

    path('', views.watched_urls_view, name='watched_urls'),
    path('watched_urls/', views.watched_urls_view, name='watched_urls'),
    path('delet/<int:id>/', views.delet, name='delet'),
    path('create_product/', views.create_product , name= 'create_product'),
    path('fetch_details_products/',views.fetch_details_products , name= 'fetch_details_products'),
    
    

]
