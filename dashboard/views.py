# dashboard/views.py
from django.shortcuts import render,get_object_or_404
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



def dataTable(request, slug=None):
    suppliers = Supplier.objects.filter(is_active=True)

    products = None
    supplier = None

    if slug:
        supplier = get_object_or_404(
            Supplier,
            slug=slug,
            is_active=True
        )
        products = supplier.products.all()   # یا Product.objects.filter(...)

    context = {
        "page_title": "داشبورد مدیریت",
        "suppliers": suppliers,
        "supplier": supplier,
        "products": products,
    }

    return render(request, "dashboard/pages/datatable.html", context)


