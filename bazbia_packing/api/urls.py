from django.urls import path
from .views import PackingAPIView

urlpatterns = [
    path("pack/", PackingAPIView.as_view(), name="pack-items"),
]

