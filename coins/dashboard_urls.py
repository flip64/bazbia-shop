from django.urls import path
from . import dashboard_views as views
from . import variant_views

app_name = "coin_catalog"
urlpatterns = [
    path("variants/lookup/", variant_views.lookup, name="variant-lookup"),
    path("variants/create/", variant_views.create, name="variant-create"),
    path("", views.catalog_list, name="list"),
    path("countries/", views.country_browser, name="countries"),
    path("<int:pk>/", views.catalog_detail, name="detail"),
    path("records/<str:kind>/", views.record_list, name="records"),
    path("records/<str:kind>/new/", views.record_edit, name="create"),
    path("records/<str:kind>/<int:pk>/", views.record_detail, name="record-detail"),
    path("records/<str:kind>/<int:pk>/edit/", views.record_edit, name="edit"),
]
