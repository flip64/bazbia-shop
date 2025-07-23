from django.urls import path
from . import category_api

urlpatterns = [
    path('categories/', category_api.category_list, name='category-list'),
]
