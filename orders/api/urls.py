from django.urls import path
from orders.api.views import WeeklyBestSellersAPIView , CartView

urlpatterns = [
    path("weeklyBestSellers/", WeeklyBestSellersAPIView.as_view(), name="weekly-best-sellers"),
    path("cart/", CartView.as_view(), name="cart"),



]

