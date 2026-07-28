# orders/api/urls.py

from django.urls import path

from orders.api import views


app_name = "orders"


urlpatterns = [
    # =====================================================
    # محصولات و پیشنهادها
    # =====================================================
    path(
        "weekly-best-sellers/",
        views.WeeklyBestSellersAPIView.as_view(),
        name="weekly-best-sellers",
    ),
    path(
        "special-offers/",
        views.SpecialOffersView.as_view(),
        name="special-offers",
    ),
    path(
        "flash-sales/",
        views.FlashSalesView.as_view(),
        name="flash-sales",
    ),

    # =====================================================
    # سبد خرید
    # =====================================================
    path(
        "cart/",
        views.CartView.as_view(),
        name="cart",
    ),
    path(
        "cart/add/",
        views.AddToCartView.as_view(),
        name="cart-add",
    ),
    path(
        "cart/items/<int:pk>/",
        views.UpdateCartItemView.as_view(),
        name="cart-item-update",
    ),
    path(
        "cart/items/<int:pk>/delete/",
        views.RemoveCartItemView.as_view(),
        name="cart-item-delete",
    ),
    path(
        "cart/clear/",
        views.ClearCartView.as_view(),
        name="cart-clear",
    ),
    path(
        "cart/save/",
        views.SaveCartView.as_view(),
        name="cart-save",
    ),
    path(
        "cart/load/",
        views.LoadSavedCartView.as_view(),
        name="cart-load",
    ),
    path(
        "cart/merge/",
        views.MergeCartView.as_view(),
        name="cart-merge",
    ),

    # =====================================================
    # سفارش‌ها
    # =====================================================
    path(
        "",
        views.OrderListView.as_view(),
        name="order-list",
    ),
    path(
        "create/",
        views.CreateOrderView.as_view(),
        name="order-create",
    ),
    path(
        "<int:pk>/",
        views.OrderDetailView.as_view(),
        name="order-detail",
    ),
    path(
        "<int:pk>/cancel/",
        views.CancelOrderView.as_view(),
        name="order-cancel",
    ),
    path(
        "track/<str:tracking_code>/",
        views.TrackOrderView.as_view(),
        name="order-track",
    ),
    path(
        "returns/",
        views.ReturnRequestView.as_view(),
        name="order-return",
    ),
]
