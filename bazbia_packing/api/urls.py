from django.urls import path

from bazbia_packing.api.views import (
    CartShippingQuoteAPIView,
    ExternalPackingAPIView,
)


app_name = "bazbia_packing"


urlpatterns = [
    path(
        "external/calculate/",
        ExternalPackingAPIView.as_view(),
        name="external-packing-calculate",
    ),
    path(
        "checkout/cart-quote/",
        CartShippingQuoteAPIView.as_view(),
        name="checkout-cart-shipping-quote",
    ),
]
