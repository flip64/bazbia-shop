from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from products.sitemaps import (
    ProductSitemap,
    CategorySitemap,
)

from core.sitemap import storefront_sitemap

sitemaps = {
    "products": ProductSitemap,
    "categories": CategorySitemap,
}


urlpatterns = [
    path('', include('core.urls', namespace='root')),
    path('admin/', admin.site.urls),
    path(
        'products/',
        include('products.urls', namespace='products')
    ),
    path(
        'schema/',
        include(
            ('schema_viewer.urls', 'schema_page'),
            namespace='schema_page'
        )
    ),
    path(
        'accounts/',
        include(
            ('core.urls', 'core'),
            namespace='core'
        )
    ),
    path(
        'orders/',
        include(
            ('orders.urls', 'orders'),
            namespace='orders'
        )
    ),
    path(
        'dashboard/',
        include(
            ('dashboard.urls', 'dashboard'),
            namespace='dashboard'
        )
    ),
    path(
        'torob_management/',
        include(
            ('torob_integration.urls', 'torob_management'),
            namespace='torob_management'
        )
    ),

    path('analytics/', include('analytics.urls')),

    # API
    path('api/products/', include('products.api.urls')),
    path(
        'api/orders/',
        include(
            'orders.api.urls',
            namespace='orders_api'
        )
    ),
    path('api/customers/', include('customers.api.urls')),
    path(
        'api/bazbia_packing/',
        include('bazbia_packing.api.urls')
    ),
    path('api/promotions/', include('promotions.api.urls')),
    path('api/payments/', include('payments.api.urls')),
    path('api/contact/', include('contact.api.urls')),
    path('api/analytics/', include('analytics.api.urls')),

    path(
        'torob_api/',
        include('torob_integration.api.urls')
    ),

    # Sitemap
    path(
        'sitemap.xml',
        storefront_sitemap,
        {'sitemaps': sitemaps},
        name='sitemap',
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
