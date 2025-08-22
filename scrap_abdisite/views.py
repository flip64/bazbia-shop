from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from scrap_abdisite.models import WatchedURL, PriceHistory
from scrap_abdisite.forms import WatchedURLForm, Create_productForm, Create_specificationsForm, Create_tagsForm
from scrap_abdisite.utils.abdi_fetcher import fetch_product_details, send_price_alert
from scrap_abdisite.utils.abdi_fetcher import extract_specifications, extract_tags
from scrap_abdisite.utils.create_product import import_products_from_json

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
@login_required
def watched_urls_view(request):
    user = request.user

    if request.method == 'POST':
        form = WatchedURLForm(request.POST, user=user)
        if form.is_valid():
            watched_url = form.save(commit=False)
            try:
                _, product_price_text = fetch_product_details(watched_url.url)
            except Exception as e:
                form.add_error('url', f'خطا در دریافت اطلاعات محصول: {e}')
                return render(request, 'scrap_abdisite/watched_urls.html', {
                    'form': form,
                    'urls': WatchedURL.objects.filter(user=user).order_by('-created_at')
                })

            cleaned_price = clean_price_text(product_price_text)
            if cleaned_price is not None:
                watched_url.price = cleaned_price
                watched_url.last_checked = timezone.now()

            watched_url.save()

            if cleaned_price is not None:
                PriceHistory.objects.create(
                    watched_url=watched_url,
                    price=cleaned_price
                )

            return redirect('scrap_abdisite:watched_urls')
    else:
        form = WatchedURLForm(user=user)

    urls = WatchedURL.objects.filter(user=user).order_by('-created_at')
    return render(request, 'scrap_abdisite/watched_urls.html', {
        'form': form,
        'urls': urls
    })


@csrf_exempt
def check_price(request):
    print(">>> check_price called")
    if request.method == 'POST':
        data = json.loads(request.body)
        url = data.get('url')
        name, new_price = fetch_product_details(url)
        new_price = clean_price_text(new_price)
        try:
            watched = WatchedURL.objects.get(url=url)
            if watched.last_price != new_price:
                watched.last_price = new_price
                watched.save()
                return JsonResponse({'changed': True})
            return JsonResponse({'changed': False})
        except WatchedURL.DoesNotExist:
            return JsonResponse({'error': 'URL not found'}, status=404)
    return JsonResponse({'error': 'Invalid method'}, status=405)


@login_required
def delet(request, id):
    url = WatchedURL.objects.get(id=id)
    url.delete()
    return redirect('/scrap_abdisite/watched_urls/')


@login_required
def check_price_all(request):
    list_url = []
    watched_urls = WatchedURL.objects.all()
    for watching in watched_urls:
        name, price = fetch_product_details(watching.url)
        price = clean_price_text(price)
        change = 'changed' if price != watching.last_price else 'not changed'
        status = {
            "name": name,
            "url": watching.url,
            "change": change,
            "price": price,
            "lastcheck": watching.last_checked
        }
        list_url.append(status)
    return JsonResponse(list_url, safe=False)


@login_required
def change_price_all(request):
    list_url = []
    watched_urls = WatchedURL.objects.all()
    for watching in watched_urls:
        name, price = fetch_product_details(watching.url)
        price = clean_price_text(price)
        if price != watching.price:
            send_status = send_price_alert(name, price, watching.price)
            send_status_email = send_status['email'] if send_status else 'not send email'
            watching.price = price
            watching.save()
            PriceHistory.objects.create(watched_url=watching, price=price)
            change = 'changed'
        else:
            change = 'not changed'
            send_status_email = 'not changed'

        status = {
            "name": name,
            "change": change,
            "lastcheck": watching.last_checked,
            "price": price,
            "sendemail_status": send_status_email
        }
        list_url.append(status)
        time.sleep(2)  # وقفه ۲ ثانیه
    return JsonResponse(list_url, safe=False)


# ===============================
# 🔹 Product Import Views
# ===============================
@login_required
def create_product(request):
    user = request.user
    if user.is_authenticated:
        import_products_from_json(user)
    return HttpResponse("Import completed successfully.")


@login_required
def create_specifications(request):
    if request.method == 'POST':
        form = Create_specificationsForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            data = json.load(file)
            count = 1
            for item in data:
                if count > 500:
                    break
                if not item.get('abdi_specifications', False):
                    product_link = item.get('product_link')
                    old_spec = item.get('specifications', [])
                    if product_link:
                        new_spec = extract_specifications(product_link)
                        merged = []
                        seen = set()
                        for spec in old_spec + new_spec:
                            if spec not in seen:
                                merged.append(spec)
                                seen.add(spec)
                        item['specifications'] = merged
                        item['abdi_specifications'] = True
                        count += 1
            response = HttpResponse(
                json.dumps(data, ensure_ascii=False, indent=2),
                content_type='application/json; charset=utf-8'
            )
            response['Content-Disposition'] = 'attachment; filename="with_features.json"'
            return response
    else:
        form = Create_specificationsForm()
    return render(request, 'scrap_abdisite/create_specifications.html', {'form': form})


@login_required
def create_tags(request):
    if request.method == 'POST':
        form = Create_tagsForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            data = json.load(file)
            count = 1
            for item in data:
                if count > 50:
                    break
                if not item.get('abdi_tags', False):
                    product_link = item.get('product_link')
                    old_tags = item.get('tags', [])
                    if product_link:
                        new_tags = extract_tags(product_link)
                        merged = []
                        seen = set()
                        for tag in old_tags + new_tags:
                            if tag not in seen:
                                merged.append(tag)
                                seen.add(tag)
                        item['tags'] = merged
                        item['abdi_tags'] = True
                        count += 1
            response = HttpResponse(
                json.dumps(data, ensure_ascii=False, indent=2),
                content_type='application/json; charset=utf-8'
            )
            response['Content-Disposition'] = 'attachment; filename="with_features.json"'
            return response
    else:
        form = Create_tagsForm()
    return render(request, 'scrap_abdisite/create_tags.html', {'form': form})


# ===============================
# 🔹 Background Script Runner
# ===============================
from scrap_abdisite.utils.scrap_abdi_site import process_latest_file, is_running

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


