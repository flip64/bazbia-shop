from django.urls import path
from .views import WeeklyBestSellersAPIView

urlpatterns = [
    path("weeklyBestSellers/", WeeklyBestSellersAPIView.as_view(), name="weekly-best-sellers"),
]
