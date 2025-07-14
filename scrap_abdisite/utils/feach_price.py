from django.utils import timezone
import requests
from bs4 import BeautifulSoup
import logging
from scrap_abdisite.models import WatchedURL, PriceHistory
from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail


def send_price_alert(name , new_price, old_price):
    """
    ارسال هشدار تغییر قیمت
    Args:
        watched_url: شیء WatchedURL
        new_price: قیمت جدید
    """
    send_status = {
        "email" :  "not send",
        "telegram" : "not send",
        "notification" : "not send",
        "consol_print ": "not send"
    }
    
    # محاسبه درصد تغییر
    change_percent = 0
    if old_price and old_price > 0:
      if old_price is not None and new_price is not None:
        diff = new_price - old_price
      else:
        # مثلا اگر اولین بار است که قیمت ذخیره شده یا قیمت ناقص است
        diff = 0
    # پیام هشدار
    
    old_price_str = f"{old_price:.2f}" if old_price is not None else "N/A"
    new_price_str = f"{new_price:.2f}" if new_price is not None else "N/A"
    

    message = (
    f"🚨 تغییر قیمت برای محصول {name or 'نامشخص'}\n"
    f"💰 قیمت قبلی: {old_price:,} تومان\n"
    f"💵 قیمت جدید: {new_price:,} تومان\n"
    f"📊 تغییر: {change_percent:+.2f}%"
)

    if old_price is None:
     message = message.replace(f"{old_price:,}", "نامشخص")
    if new_price is None:
     message = message.replace(f"{new_price:,}", "نامشخص")
    if change_percent is None:
     message = message.replace(f"{change_percent:+.2f}%", "نامشخص")

    # اینجا می‌توانید روش‌های مختلف ارسال هشدار را پیاده‌سازی کنید

    #    print(message)
    send_email_status = send_email_view(message)     # - ارسال ایمیل

    # مثلاً:
    # - ارسال نوتیفیکیشن درون‌برنامه‌ای
    # - ارسال به سرویس‌های پیام‌رسان (مثل Telegram, SMS)
    
    # print(f"ارسال هشدار به کاربر {user.email}:\n{message}")  # برای دیباگ
    
    # مثال ارسال به تلگرام:
    # send_telegram_alert(user.telegram_chat_id, message)

    send_status["email"] = send_email_status

    return send_status

def send_email_view(message):
    send_mail(
        ' تغییر قیمت  ',
        message,
        'jr64.namderloo@gmail.com',
        ['jr64.naderloo@gmail.com'],
        fail_silently=False,
    )
    
    return ("ایمیل با موفقیت ارسال شد!")


def fetch_product_details(url):
    print(f"Fetching URL: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/115.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"خطا در دریافت صفحه: {e}")
        return None, None

    soup = BeautifulSoup(response.text, "html.parser")

    # استخراج نام محصول
    name_tag = soup.find("h1", class_="product_title")
    product_name = name_tag.text.strip() if name_tag else None



    # جستجوی چندگانه برای کلاس‌های ممکن قیمت
    if "ناموجود" in soup.text or "تمام شد" in soup.text:
       product_price = "0"
    else:   
      price_tag = soup.find("span", class_="woocommerce-Price-amount amount")
      if not price_tag:
        price_tag = soup.find("span", class_="woocommerce-Price-amount")
      product_price = price_tag.text.strip() if price_tag else None
 

    if not product_name and not product_price:
        print("نام و قیمت محصول یافت نشد.")
    elif not product_name:
        print("نام محصول یافت نشد.")
    elif not product_price:
        print("قیمت محصول یافت نشد.")
    

    return product_name, product_price


logger = logging.getLogger(__name__)

def check_price_changes():
    """
    بررسی تغییرات قیمت برای تمام URLهای کاربر (یا همه کاربران)
    Args:
        user: اگر مشخص شود فقط URLهای این کاربر بررسی می‌شود
    Returns:
        dict: آمار عملیات
    """
    # فیلتر URLها بر اساس کاربر
    queryset = WatchedURL.objects.all()
    stats = {
        'total_checked': 0,
        'price_changed': 0,
        'new_products': 0,
        'errors': 0
    }

    for watched_url in queryset:
        try:
            with transaction.atomic():
                # دریافت اطلاعات محصول از سایت هدف
                product_name ,current_price = fetch_product_details(watched_url.url)

                stats['total_checked'] += 1

                
                # اگر قیمت تغییر کرده باشد
                if watched_url.last_price != current_price:
                    # ثبت تاریخچه جدید
                    PriceHistory.objects.create(
                        watched_url=watched_url,
                        price=current_price
                    )
                    
                    # آپدیت آخرین قیمت و زمان بررسی
                    watched_url.last_price = current_price
                    watched_url.last_checked = timezone.now()
                    watched_url.save()
                    
                    stats['price_changed'] += 1
                    
                    # ارسال هشدار
                    send_price_alert(watched_url, current_price)
                    
        except Exception as e:
            logger.error(f"Error processing {watched_url.url}: {str(e)}")
            stats['errors'] += 1

    return stats