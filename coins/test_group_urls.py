from django.urls import path, include
from .test_urls import urlpatterns as existing
urlpatterns = [*existing, path('api/products/', include('products.api.urls'))]
