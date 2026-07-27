from django.urls import path

from bazbia_packing.api.views import (
    CartShippingQuoteAPIView,
    ExternalPackingAPIView,
)


app_name = "bazbia_packing"


urlpatterns = [
    # API عمومی برای شرکت‌ها و سرویس‌های خارجی
    # فعلاً غیرفعال است.
    path(
        "external/calculate/",
        ExternalPackingAPIView.as_view(),
        name="external-packing-calculate",
    ),

    # API داخلی فروشگاه بازبیا
    path(
        "checkout/cart-quote/",
        CartShippingQuoteAPIView.as_view(),
        name="checkout-cart-shipping-quote",
    ),
]
