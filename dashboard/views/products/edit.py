from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render





@login_required
def product_edit(request, pk):
    """
    ویرایش یک محصول.
    """

    context = {
        "page_title": "ویرایش محصول",
        "product_id": pk,
    }

    return render(
        request,
        "dashboard/pages/product_edit.html",
        context,
    )
