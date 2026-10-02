from django.urls import path

from bale_integration.views import bale_webhook


app_name = "bale_integration"

urlpatterns = [
    path("webhook/<str:secret>/", bale_webhook, name="webhook"),
]
