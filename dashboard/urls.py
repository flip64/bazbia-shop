from django.urls import path
from dashboard.views  import  dashboard,dataTable
app_name = "dashboard"

urlpatterns = [
    
    path('', dashboard , name='dashboard'),
    path('suppliers/', dashboard , name='supplers'),
    path('datatables/<slug:slug>/',dataTable, name='datatable'),



]
