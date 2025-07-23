from django.urls import path
from . import category_api

urlpatterns = [
    path('categories/', category_api.list_categories, name='list_categories'),
]
