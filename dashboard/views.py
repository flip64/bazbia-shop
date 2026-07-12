# dashboard/views.py
from django.shortcuts import render,get_object_or_404
from django.contrib.auth.decorators import login_required
from suppliers.models import Supplier
from products.models import Product

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
            name=slug,
            is_active=True
        )
        products = Product.objects.filter(variants__supplier_offers__supplier=supplier
        ).distinct()
   

    context = {
        "page_title": "داشبورد مدیریت",
        "suppliers": suppliers,
        "supplier": supplier,
        "products": products,
    }

    return render(request, "dashboard/pages/datatable.html", context)


