# -*- coding: utf-8 -*-

from django.urls import path

from dashboard.views import (
    dashboard_home,
    import_dashboard,
    offer_price_history,
    operation_logs,
    price_history_list,
    product_detail,
    product_edit,
    product_list,
    product_price_manager,
    product_profit_manager,
    supplier_detail,
    supplier_list,
    supplier_products,
    sync_dashboard,
)

app_name = "dashboard"

urlpatterns = [
    path(
        "",
        dashboard_home,
        name="home",
    ),
    path(
        "products/",
        product_list,
        name="product_list",
    ),
    path(
        "products/profit/",
        product_profit_manager,
        name="product_profit",
    ),
    path(
        "products/prices/",
        product_price_manager,
        name="product_price",
    ),
    path(
        "products/<int:pk>/",
        product_detail,
        name="product_detail",
    ),
    path(
        "products/<int:pk>/edit/",
        product_edit,
        name="product_edit",
    ),
    path(
        "suppliers/",
        supplier_list,
        name="supplier_list",
    ),
    path(
        "suppliers/<slug:slug>/",
        supplier_detail,
        name="supplier_detail",
    ),
    path(
        "suppliers/<slug:slug>/products/",
        supplier_products,
        name="supplier_products",
    ),
    path(
        "price-history/",
        price_history_list,
        name="price_history",
    ),
    path(
        "offers/<int:offer_id>/price-history/",
        offer_price_history,
        name="offer_price_history",
    ),
    path(
        "sync/",
        sync_dashboard,
        name="sync",
    ),
    path(
        "import/",
        import_dashboard,
        name="import",
    ),
    path(
        "logs/",
        operation_logs,
        name="logs",
    ),
]