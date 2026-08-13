from django.urls import path
from dashboard.views  import  dashboard,supplier_datatable  
app_name = "dashboard"

urlpatterns = [
    
    path('', dashboard , name='dashboard'),
    path('suppliers/', dashboard , name='suppliers'),
    path('datatables/<slug:slug>/',supplier_datatable, name='datatable'),



]
