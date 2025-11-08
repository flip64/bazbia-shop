from django.urls import path
from . import views

urlpatterns = [
    path('watched-urls/all/', views.watched_urls_all_api, name='watched_urls_all_api'),
  # API برای بروزرسانی قیمت یک WatchedURL مشخص
    path('watched-url/<int:pk>/update-price/', views.UpdateWatchedURLPriceAPIView.as_view(), name='update_watched_url_price_api'),
    
]
