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




    
urlpatterns = [
    path('', include('core.urls', namespace='root')),
    path('admin/', admin.site.urls),
    path('products/', include('products.urls', namespace='products')),
    path('scrap_abdisite/', include('scrap_abdisite.urls', namespace='scrap_abdisite')),
    path('schema/', include(('schema_viewer.urls', 'schema_page'), namespace='schema_page')),
    path('accounts/', include(('core.urls', 'core'), namespace='core')),# آدرس‌های مربوط به login/signup
    path('orders/', include(('orders.urls', 'orders'), namespace='orders')),# آدرس‌های مربوط به orders

    


   


    # مسیرهای api
    path('api/products/', include('products.api.urls')),
    path('api/orders/', include('orders.api.urls')),
    path('api/customers/', include('customers.api.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

   

