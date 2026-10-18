from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path(
        "dashboard/",
        include(
            ([path("coins/", include("coins.dashboard_urls"))], "dashboard"),
            namespace="dashboard",
        ),
    ),
    path("api/orders/", include("orders.api.urls")),
    path("admin/", admin.site.urls),
    path("api/coins/", include("coins.api.urls")),
]
