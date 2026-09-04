"""
URL configuration for bazbia_shop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path ,include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from products.sitemaps import ProductSitemap, CategorySitemap




sitemaps = {
    "products": ProductSitemap,
    
}



    
urlpatterns = [
    path('', include('core.urls', namespace='root')),
    path('admin/', admin.site.urls),
    path('products/', include('products.urls', namespace='products')),
    path('schema/', include(('schema_viewer.urls', 'schema_page'), namespace='schema_page')),
    path('accounts/', include(('core.urls', 'core'), namespace='core')),# آدرس‌های مربوط به login/signup
    path('orders/', include(('orders.urls', 'orders'), namespace='orders')),# آدرس‌های مربوط به orders
    path('dashboard/', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),# آدرس‌های مربوط به مدیریت
    path('torob_management/', include(('torob_integration.urls', 'torob_management'), namespace='torob_management')),# آدرس‌های مربوط به مدیریت
    path('analytics/', include("analytics.urls")),


   


    # مسیرهای api
    path('api/products/', include('products.api.urls')),
    path('api/orders/', include(('orders.api.urls'),namespace='orders_api')), 
    path('api/customers/', include('customers.api.urls')),
    path('api/bazbia_packing/',include('bazbia_packing.api.urls')),
    path('api/promotions/', include('promotions.api.urls')),
    path('api/payments/',include('payments.api.urls')),
    path("api/contact/", include("contact.api.urls")),
    path("api/analytics/", include("analytics.api.urls")),
    
    path("torob_api/",include("torob_integration.api.urls")),

    path("sitemap.xml", sitemap, {"sitemaps": sitemaps},name="django.contrib.sitemaps.views.sitemap"),

    
]




if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

   

