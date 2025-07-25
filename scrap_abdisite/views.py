from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import WatchedURL, PriceHistory
from scrap_abdisite.form import WatchedURLForm
from django.contrib.auth.decorators import login_required
from scrap_abdisite.utils.feach_price import fetch_product_details,send_price_alert
from django.utils import timezone
import time
import re
import json




@login_required
def watched_urls_view(request):
    user = request.user

    if request.method == 'POST':
        form = WatchedURLForm(request.POST, user=user)
        if form.is_valid():
            watched_url = form.save(commit=False)

            # فقط قیمت را از تابع دریافت می‌کنیم، نام محصول فعلاً نادیده گرفته می‌شود
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

def clean_price_text(price_text):
    """
    تبدیل قیمت مثل "850,000 ریال" به 850000 (عدد صحیح بزرگ)
    """
    if not price_text:
        return None
    cleaned = re.sub(r'[^\d]', '', price_text)
    return int(cleaned) if cleaned.isdigit() else None


@csrf_exempt
def check_price(request):
    print(">>> check_price called")
    if request.method == 'POST':
        data = json.loads(request.body)
        url = data.get('url')
        name , new_price = fetch_product_details(url) 
        new_price = clean_price_text(new_price) 
        try:
            # اگر می‌خوای بررسی کاربر هم باشه باید user رو از request بدست بیاری (اگر احراز هویت هست)
            watched = WatchedURL.objects.get(url=url)
            if watched.last_price != new_price:
                watched.last_price = new_price
                watched.save()
                return JsonResponse({'changed': True})
            return JsonResponse({'changed': False})
        except WatchedURL.DoesNotExist:
            return JsonResponse({'error': 'URL not found'}, status=404)

    return JsonResponse({'error': 'Invalid method'}, status=405)


def delet(request , id):
   url = WatchedURL.objects.get(id=id)
   url.delete()
   return redirect('/scrap_abdisite/watched_urls/')
 
def check_price_all(request):
    list_url = []
    wached_urls = WatchedURL.objects.all()
    for waching in wached_urls:
       name , price =fetch_product_details(waching.url)
       price = clean_price_text(price)
       if price != waching.last_price :
           change = 'chanjed'
       else :
           change ='not chanjed'


       status = {
         "name"     : name ,
         "url"      : waching.url,
         "change"   : change,
         "price"    : price , 
         "lastcheck": waching.last_checked
       } 
       list_url.append(status)
    

    return JsonResponse(list_url , safe=False ) 

def change_price_all(request):
    list_url = []
    wached_urls = WatchedURL.objects.all()
    for waching in wached_urls:
       name , price =fetch_product_details(waching.url)
       price = clean_price_text(price)
       if price != waching.price :
           
           send_status = send_price_alert(name,price,waching.price)
           if(send_status) : 
               send_status_email= send_status['email']
           else: 
               send_status_email = 'not send email' 
           
           waching.price = price
           waching.save()
           PriceHistory.objects.create(watched_url=waching,price=price)
           change = 'chanjed'
       else :
           change ='not chanjed'
           send_status_email = 'not changed'


       status = {
         "name"   : name,
         "change"   : change,
         "lastcheck": waching.last_checked , 
         "price"    : price ,
         "sendemail_status" : send_status_email
       } 
       list_url.append(status)
       time.sleep(2)  # وقفه به مدت ۳ ثانیه


    return JsonResponse(list_url , safe=False ) 

