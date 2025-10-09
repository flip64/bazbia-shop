from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from threading import Thread
import re
from scrap_abdisite.models import WatchedURL
from products.models import ProductVariant, Product, ProductImage
from django.core.paginator import Paginator
from django.core.files.storage import default_storage


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


# ===============================
# 🔹 Product Image Management (by slug)
# ===============================
@login_required
def product_images_list(request):
    """
    نمایش لیست همه محصولات دارای تصویر
    """
    query = request.GET.get("q", "")
    products = Product.objects.filter(images__isnull=False).distinct()
    if query:
        products = products.filter(name__icontains=query)

    paginator = Paginator(products, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "query": query,
    }
    return render(request, "scrap_abdisite/product_images.html", context)


@login_required
def product_images_by_slug(request, slug):
    """
    نمایش تمام تصاویر مربوط به یک محصول خاص (بر اساس slug)
    """
    product = get_object_or_404(Product, slug=slug)
    images = product.images.all()  # فرض بر این است که related_name='images' در ProductImage وجود دارد

    context = {
        "product": product,
        "images": images,
    }
    return render(request, "scrap_abdisite/product_images_detail.html", context)


@login_required
@require_POST
def product_image_update_by_slug(request, slug, image_id):
    """
    آپدیت تصویر محصول بر اساس slug و شناسه تصویر
    """
    product = get_object_or_404(Product, slug=slug)
    image_obj = get_object_or_404(product.images, id=image_id)

    new_file = request.FILES.get("image")
    if not new_file:
        messages.error(request, "هیچ تصویری انتخاب نشده است.")
        return redirect("scrap_abdisite:product_images_by_slug", slug=slug)

    old_path = image_obj.image.name
    if default_storage.exists(old_path):
        default_storage.delete(old_path)

    saved_path = default_storage.save(old_path, new_file)
    image_obj.image.name = saved_path
    image_obj.save()

    messages.success(request, f"✅ تصویر محصول '{product.name}' بروزرسانی شد.")
    return redirect("scrap_abdisite:product_images_by_slug", slug=slug)
