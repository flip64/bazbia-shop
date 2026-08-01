from django.urls import path

from .views import torob_variant_management


app_name = "torob_management"

urlpatterns = [
    path(
        "variants/",
        torob_variant_management,
        name="variants",
    ),
]
