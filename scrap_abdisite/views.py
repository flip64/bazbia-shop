from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from django.utils import timezone
from scrap_abdisite.models import WatchedURL, PriceHistory
from scrap_abdisite.forms import WatchedURLForm
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from products.models import ProductVariant
from suppliers.models import Supplier

import time
import re
import json
from threading import Thread


# ===============================
# 🔹 Utility Functions
# ===============================
def clean_price_text(price_text):
    """
    تبدیل قیمت مثل "850,000 ریال" به 850000 (عدد صحیح بزرگ)
    """
    if not price_text:
        return None
    cleaned = re.sub(r'[^\d]', '', price_text)
    return int(cleaned) if cleaned.isdigit() else None


# ===============================
# 🔹 Watched URLs Views
# ===============================
@require_POST
def watched_urls_update(request, watched_id):
    """
    بروزرسانی قیمت محصول بر اساس رکورد WatchedURL
    """
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


def product_price_list(request):
    # select_related برای بهینه‌سازی joinها
    watched = WatchedURL.objects.select_related('variant', 'variant__product', 'supplier').all()
    return render(request, "scrap_abdisite/watched_urls.html", {"products": watched})


def delet(request, id):
    url = get_object_or_404(WatchedURL, id=id)
    url.delete()
    messages.success(request, "رکورد حذف شد.")
    return redirect('scrap_abdisite:product_price_list')






        variant.save()
        messages.success(request, f"قیمت‌های {variant.product.name} بروزرسانی شد.")

    except ValueError:
        messages.error(request, "ورودی معتبر نیست.")

    return redirect('scrap_abdisite:product_price_list')

@login_required
def delet(request, id):
    url = WatchedURL.objects.get(id=id)
    url.delete()
    return redirect('/scrap_abdisite/watched_urls/')



# ===============================
# 🔹 Product Import Views
# ===============================
@login_required
def create_product(request):
    user = request.user
    if user.is_authenticated:
      print("ok for fetch")
      #  fetche_productsـlist()
      #  process_latest_file()   
      #  import_products_from_json(user)
        
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



