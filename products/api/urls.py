from django.urls import path
from . import category_api



    
urlpatterns = [
    path('categories/', category_api.list_categories, name='list_categories_api'),
    path('import-categories/', category_api.import_categories, name='import-categories'),




]





