from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from threading import Thread
import re
from scrap_abdisite.models import WatchedURL
from products.models import ProductVariant
from django.core.paginator import Paginator


# ===============================
# 🔹 Utility Function
# ===============================
def clean_price_text(price_text):
    """
    تبدیل قیمت مثل "850,000 ریال" به 850000
    """
    if not price_text:
        return None
    cleaned = re.sub(r'[^\d]', '', price_text)
    return int(cleaned) if cleaned.isdigit() else None


# ===============================
# 🔹 Views
# ===============================


def product_price_list(request):
    """
    نمایش لیست لینک‌های پایش شده محصولات
    - امکان جستجو فقط روی نام محصول
    - نمایش Pagination
    """
    query = request.GET.get('q', '')

    # فیلتر روی نام محصول (variant__product__name)
    watched_list = WatchedURL.objects.select_related(
        'variant', 'variant__product', 'supplier'
    )
    if query:
        watched_list = watched_list.filter(variant__product__name__icontains=query)

    # Pagination: هر صفحه 20 رکورد
    paginator = Paginator(watched_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,  # برای فرم جستجو
    }
    return render(request, "scrap_abdisite/watched_urls.html", context)




@require_POST
def watched_urls_update(request, watched_id):
    watched = get_object_or_404(WatchedURL, id=watched_id)
    variant = watched.variant

    if not variant:
        messages.error(request, "این لینک واریانت ندارد.")
        return redirect("scrap_abdisite:product_price_list")

    try:
        price = request.POST.get('price')
        discount_price = request.POST.get('discount_price')

        if price:
            variant.price = int(price)

        if discount_price:
            dp = int(discount_price)
            if dp > variant.price:
                messages.error(request, "قیمت تخفیف نمی‌تواند بیشتر از قیمت اصلی باشد.")
                return redirect("scrap_abdisite:product_price_list")
            variant.discount_price = dp
        else:
            variant.discount_price = None

        variant.save()
        messages.success(request, f"قیمت‌های {variant.product.name} بروزرسانی شد.")

    except ValueError:
        messages.error(request, "ورودی معتبر نیست.")

    return redirect("scrap_abdisite:product_price_list")


@login_required
def delet(request, watched_id):
    url = get_object_or_404(WatchedURL, id=watched_id)
    url.delete()
    messages.success(request, "رکورد حذف شد.")
    return redirect('scrap_abdisite:product_price_list')


# ===============================
# 🔹 Product Import Views
# ===============================
@login_required
def create_product(request):
    user = request.user
    if user.is_authenticated:
        print("ok for fetch")
        # fetche_products_list()
        # process_latest_file()   
        # import_products_from_json(user)
        
    return HttpResponse("Import completed successfully.")


# ===============================
# 🔹 Background Script Runner
# ===============================
def fetch_details_products(request):
    global is_running
    if is_running:
        return JsonResponse({"status": "running", "message": "اسکریپت در حال اجراست"})

    def run():
        global is_running
        is_running = True
        try:
            process_latest_file()
        finally:
            is_running = False

    Thread(target=run).start()
    return JsonResponse({"status": "started", "message": "اسکریپت در پس‌زمینه شروع شد"})
