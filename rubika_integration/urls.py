from django.urls import path

from rubika_integration.views import rubika_webhook


app_name = "rubika_integration"

urlpatterns = [
    path("webhook/<str:secret>/", rubika_webhook, name="webhook"),
]
