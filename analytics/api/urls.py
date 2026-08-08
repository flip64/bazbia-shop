from django.urls import path

from analytics.api.views import SiteEventCreateAPIView


app_name = "analytics"


urlpatterns = [
    path(
        "events/",
        SiteEventCreateAPIView.as_view(),
        name="event-create",
    ),
]
