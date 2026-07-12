# dashboard/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from suppliers.models import Supplier
@login_required
def dashboard(request):
    suppliers = Supplier.objects.filter(is_active=True)

    
    context = {
        "page_title": "محصولات ",
        "suppliers":suppliers
        
    }
    return render(request, "dashboard/index.html", context)


def dataTable(request):
    suppliers = Supplier.objects.filter(is_active=True)

    
    context = {
        "page_title": "داشبورد مدیریت",
        "suppliers":suppliers
    }
    return render(request, "dashboard/pages/datatable.html", context)
