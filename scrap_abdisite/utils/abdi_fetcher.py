from django.utils import timezone
import requests
from bs4 import BeautifulSoup
import logging
from scrap_abdisite.models import WatchedURL, PriceHistory
from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail





logger = logging.getLogger(__name__)

# کش ساده برای نگهداری soup ها
_soup_cache = {}

def get_soup(url):
    """
    دریافت یا بازگرداندن BeautifulSoup مربوط به یک URL.
    - اگر قبلاً برای همین URL ساخته شده باشد، همان را برمی‌گرداند.
    - در غیر اینصورت درخواست جدید می‌زند و کش می‌کند.
    """
    if url in _soup_cache:
        soup = _soup_cache[url]
        if getattr(soup, "source_url", None) == url:
            return soup

    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    soup.source_url = url
    _soup_cache[url] = soup
    print('send request')
    return soup




def clean_price(price_str):
    if not price_str:
        return None
    digits = re.sub(r"[^\d]", "", price_str)  # حذف غیرعددی‌ها
    return int(digits) if digits else None



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



def extract_specifications(url):
    
    soup = get_soup(url)
    feature_list = []

    # جستجو برای بخش "ویژگی های محصول"
    section_title = soup.find(text=lambda t: "ویژگی های محصول" in t)
    if section_title:
        ul = section_title.find_next("ul")
        if ul:
            for li in ul.find_all("li"):
                if ":" in li.text:
                    key, val = li.text.split(":", 1)
                    feature_list.append(f"{key.strip()}: {val.strip()}")

    return feature_list


def extract_tags(url):
    
    soup = get_soup(url)
    tags = []

    # تگ‌ها معمولا در بخش "برچسب: ..." هستند و دارای rel="tag" هستند
    tag_links = soup.find_all("a", rel="tag")
    for tag in tag_links:
        text = tag.get_text(strip=True)
        if text:
            tags.append(text)

    return tags


def extract_product_images(url):

    soup = get_soup(url)
    image_links = []

    # جستجوی تصاویر در گالری محصول
    gallery_divs = soup.find_all("div", class_="woocommerce-product-gallery__image")
    for div in gallery_divs:
        img_tag = div.find("img")
        if img_tag and img_tag.get("src"):
            image_links.append(img_tag["src"])

    # اگر چیزی پیدا نشد، می‌توانیم تصویر اصلی را هم بررسی کنیم
    if not image_links:
        main_img = soup.find("img", class_="wp-post-image")
        if main_img and main_img.get("src"):
            image_links.append(main_img["src"])

    return image_links


def check_priceـproduct(url):
    """
    بررسی تغییر قیمت برای یک محصول خاص با استفاده از URL
    Args:
        url (str): آدرس محصول (WatchedURL.url)
    Returns:
        dict: نتیجه بررسی (new_product, price_changed, no_change یا error)
    """
    try:
        watched_url = WatchedURL.objects.get(url=url)

        product_name, current_price = fetch_product_details(watched_url.url)

        result = {
            "url": watched_url.url,
            "name": product_name,
            "old_price": watched_url.last_price,
            "new_price": current_price,
            "status": "no_change"
        }

        # اگر محصول تازه بود (last_price تهی است)
        if watched_url.last_price is None:
            watched_url.last_price = current_price
            watched_url.last_checked = timezone.now()
            watched_url.save()
            result["status"] = "new_product"
            return result

        # اگر قیمت تغییر کرده باشد
        if watched_url.last_price != current_price:
            PriceHistory.objects.create(
                watched_url=watched_url,
                price=current_price
            )
            watched_url.last_price = current_price
            watched_url.last_checked = timezone.now()
            watched_url.save()

            result["status"] = "price_changed"
            send_price_alert(watched_url, current_price)

        return result

    except WatchedURL.DoesNotExist:
        return {"error": f"WatchedURL with url={url} not found"}
    except Exception as e:
        logger.exception(f"Error checking price for url={url}")
        return {"error": str(e)}




def fetch_product_details(url):
  
    soup = get_soup(url)

    # استخراج نام محصول
    name_tag = soup.find("h1", class_="product_title")
    product_name = name_tag.text.strip() if name_tag else None

    # جستجوی چندگانه برای کلاس‌های ممکن قیمت
    if "ناموجود" in soup.text or "تمام شد" in soup.text:
        product_price = 0
    else:
        price_tag = soup.find("span", class_="woocommerce-Price-amount amount")
        if not price_tag:
            price_tag = soup.find("span", class_="woocommerce-Price-amount")

        product_price = clean_price(price_tag.text) if price_tag else None

    if not product_name and not product_price:
        print("نام و قیمت محصول یافت نشد.")
    elif not product_name:
        print("نام محصول یافت نشد.")
    elif not product_price:
        print("قیمت محصول یافت نشد.")

    return product_name, product_price

