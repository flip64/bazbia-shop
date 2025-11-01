# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from threading import Thread
from django.core.paginator import Paginator
from django.core.files.storage import default_storage
import re

from scrap_abdisite.models import WatchedURL
from products.models import Product, ProductVariant
from django.core.cache import cache


@login_required
@require_POST
def toggle_product_status(request, product_id):
    """فعال یا غیرفعال کردن محصول با کلیک روی دکمه در جدول"""
    product = get_object_or_404(Product, id=product_id)
    product.is_active = not product.is_active
    product.save(update_fields=["is_active"])
    return JsonResponse({
        "status": "ok",
        "is_active": product.is_active
    })


# ===============================
# Utility Function
# ===============================
def clean_price_text(price_text):
    """تبدیل قیمت مانند '850,000 ریال' یا '۱۲۳٬۰۰۰ تومان' به عدد صحیح"""
    if not price_text:
        return None
    cleaned = re.sub(r"[^\d]", "", str(price_text))
    try:
        return int(cleaned)
    except ValueError:
        return None


# ===============================
# Views - Watched URLs / Price
# ===============================
def product_price_list(request):
    """نمایش لیست لینک‌های پایش شده محصولات با قابلیت جستجو و صفحه‌بندی"""
    query = request.GET.get('q', '')
    watched_list = WatchedURL.objects.select_related('variant', 'variant__product', 'supplier')
    

    if query:
        watched_list = watched_list.filter(variant__product__name__icontains=query)

    paginator = Paginator(watched_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "scrap_abdisite/watched_urls.html", {
        'page_obj': page_obj,
        'query': query,
    })


@login_required
def delete_watched_url(request, watched_id):
    """حذف رکورد WatchedURL"""
    url = get_object_or_404(WatchedURL, id=watched_id)
    url.delete()
    messages.success(request, "رکورد با موفقیت حذف شد.")
    return redirect('scrap_abdisite:product_price_list')


# ===============================
# Product Import Views
# ===============================
@login_required
def create_product(request):
    user = request.user
    if user.is_authenticated:
        try:
            # fetche_products_list()
            # process_latest_file()
            # import_products_from_json(user)
            messages.success(request, "محصولات با موفقیت ایمپورت شدند.")
        except Exception as e:
            messages.error(request, f"خطا در ایمپورت: {e}")
    return HttpResponse("Import completed successfully.")


# ===============================
# Background Script Runner
# ===============================
def fetch_details_products(request):
    """اجرای فرآیند پردازش در پس‌زمینه فقط اگر در حال اجرا نباشد"""
    if cache.get("is_running_script"):
        return JsonResponse({"status": "running", "message": "اسکریپت در حال اجراست"})

    def run():
        cache.set("is_running_script", True, timeout=3600)
        try:
            process_latest_file()
        finally:
            cache.delete("is_running_script")

    Thread(target=run).start()
    return JsonResponse({"status": "started", "message": "اسکریپت در پس‌زمینه شروع شد"})


# ===============================
# Product Image Management (by slug)
# ===============================
@login_required
def product_images_by_slug(request, slug):
    """نمایش همه تصاویر یک محصول بر اساس slug"""
    product = get_object_or_404(Product, slug=slug)
    images = product.images.only("id", "image")

    paginator = Paginator(images, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "scrap_abdisite/product_images_detail.html", {
        "product": product,
        "page_obj": page_obj,
    })


@login_required
@require_POST
def product_image_update_by_slug(request, slug, image_id):
    """بروزرسانی تصویر محصول بر اساس slug و id تصویر"""
    product = get_object_or_404(Product, slug=slug)
    image_obj = get_object_or_404(product.images, id=image_id)

    new_file = request.FILES.get("image")
    if not new_file:
        messages.error(request, "هیچ تصویری انتخاب نشده است.")
        return redirect("scrap_abdisite:product_images_by_slug", slug=slug)

    old_path = image_obj.image.name

    # حذف فایل قبلی اگر وجود دارد
    if default_storage.exists(old_path):
        try:
            default_storage.delete(old_path)
        except Exception as e:
            messages.warning(request, f"خطا در حذف فایل قبلی: {e}")

    # بازنویسی مستقیم (بدون ساخت فایل جدید)
    try:
        with default_storage.open(old_path, "wb") as f:
            for chunk in new_file.chunks():
                f.write(chunk)
    except Exception as e:
        messages.error(request, f"خطا در بروزرسانی تصویر: {e}")
        return redirect("scrap_abdisite:product_images_by_slug", slug=slug)

    # بروزرسانی مسیر در مدل
    image_obj.image.name = old_path
    image_obj.save(update_fields=["image"])

    messages.success(request, f"تصویر محصول '{product.name}' با موفقیت بروزرسانی شد.")
    return redirect("scrap_abdisite:product_images_by_slug", slug=slug)
