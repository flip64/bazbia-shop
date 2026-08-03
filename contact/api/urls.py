from django.urls import path

from contact.api.views import (
    ContactMessageCreateAPIView,
)


app_name = "contact_api"


urlpatterns = [
    path(
        "messages/",
        ContactMessageCreateAPIView.as_view(),
        name="message-create",
    ),
]
