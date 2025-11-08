from django.urls import path
from . import views

urlpatterns = [
    path('watched-urls/all/', views.watched_urls_all_api, name='watched_urls_all_api'),
]
