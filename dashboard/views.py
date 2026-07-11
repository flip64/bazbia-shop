# dashboard/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from suppliers.models import Supplier
@login_required
def dashboard(request):
    suppliers = Supplier.objects.filter(is_active=True)

    
    context = {
        "page_title": "داشبورد مدیریت",
        "supplers":suppliers
    }
    return render(request, "dashboard/index.html", context)
