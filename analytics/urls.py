# analytics/urls.py

from django.urls import path

from analytics.views import analytics_dashboard


app_name = "analytics"


urlpatterns = [
    path(
        "",
        analytics_dashboard,
        name="dashboard",
    ),
]
