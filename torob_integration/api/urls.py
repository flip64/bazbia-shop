from django.urls import path

from .views import TorobProductsAPIView


app_name = "torob_integration_api"

urlpatterns = [
    path("v3/products",TorobProductsAPIView.as_view(),name="products-v3"),
]
