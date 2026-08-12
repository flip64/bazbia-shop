# dashboard/views.py
from django.shortcuts import render,get_object_or_404
from django.contrib.auth.decorators import login_required
from suppliers.models import Supplier
from suppliers.models import SupplierOffer

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
                

        product_offers = (SupplierOffer.objects.filter(supplier=supplier)
                  .select_related("variant", "variant__product"))
        
        



    context = {
        "page_title": "داشبورد مدیریت",
        "suppliers": suppliers,
        "supplier": supplier,
        "product_offers": product_offers,
    }              

        

        
        
        
        


    return render(request, "dashboard/pages/datatable.html", context)


