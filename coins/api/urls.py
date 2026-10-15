from django.urls import path
from . import views

app_name = "coins_api"
urlpatterns = [
    path("", views.CoinListView.as_view(), name="list"),
    path("filters/", views.FilterView.as_view(), name="filters"),
    path("packs/", views.PackListView.as_view(), name="pack-list"),
    path("packs/<slug:slug>/", views.PackDetailView.as_view(), name="pack-detail"),
    path("<slug:slug>/", views.CoinDetailView.as_view(), name="detail"),
]
