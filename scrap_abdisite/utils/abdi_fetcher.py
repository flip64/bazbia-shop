import requests
from bs4 import BeautifulSoup
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

# کش ساده برای نگهداری soup ها
_soup_cache = {}

def get_soup(url):
    """دریافت یا بازگرداندن BeautifulSoup مربوط به یک URL"""
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
    print("send request")
    return soup

def clean_price(price_str):
    if not price_str:
        return None
    digits = re.sub(r"[^\d]", "", price_str)
    return int(digits) if digits else None

def send_price_alert(name, new_price, old_price):
    """ارسال هشدار تغییر قیمت (فعلاً فقط چاپ در کنسول)"""
    change_percent = 0
    if old_price and old_price > 0 and new_price is not None:
        diff = new_price - old_price
        change_percent = (diff / old_price) * 100

    message = (
        f"🚨 تغییر قیمت برای محصول {name or 'نامشخص'}\n"
        f"💰 قیمت قبلی: {old_price or 'نامشخص'} تومان\n"
        f"💵 قیمت جدید: {new_price or 'نامشخص'} تومان\n"
        f"📊 تغییر: {change_percent:+.2f}%"
    )

    print(message)
    return {"console": "sent"}

def extract_specifications(url):
    soup = get_soup(url)
    feature_list = []

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
    tags = [tag.get_text(strip=True) for tag in soup.find_all("a", rel="tag")]
    return tags

def extract_product_images(url):
    soup = get_soup(url)
    image_links = []

    gallery_divs = soup.find_all("div", class_="woocommerce-product-gallery__image")
    for div in gallery_divs:
        img_tag = div.find("img")
        if img_tag and img_tag.get("src"):
            image_links.append(img_tag["src"])

    if not image_links:
        main_img = soup.find("img", class_="wp-post-image")
        if main_img and main_img.get("src"):
            image_links.append(main_img["src"])
    return image_links

def fetch_product_details(url):
    soup = get_soup(url)

    # نام محصول
    name_tag = soup.find("h1", class_="product_title")
    product_name = name_tag.text.strip() if name_tag else None

    # قیمت محصول
    if "ناموجود" in soup.text or "تمام شد" in soup.text:
        product_price = 0
    else:
        price_tag = soup.find("span", class_="woocommerce-Price-amount amount")
        if not price_tag:
            price_tag = soup.find("span", class_="woocommerce-Price-amount")
        product_price = clean_price(price_tag.text) if price_tag else None

    return product_name, product_price


def extract_quantity(product_link):
    resp = requests.get(product_link, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # پیدا کردن المان موجودی
    # مثال: span یا div ای که متن "در انبار" دارد
    stock_elem = soup.find(lambda tag: tag.name in ["span", "div", "p", "li"] 
                           and "در انبار" in tag.get_text())
    if not stock_elem:
        return None

    text = stock_elem.get_text().strip()
    # متن ممکن است مثل "128 در انبار"
    match = re.search(r"(\d+)\s*در انبار", text)
    if match:
        return int(match.group(1))
    else:
        # اگر فرمت متفاوت باشد، تلاش دیگری
        match2 = re.search(r"(\d+)", text)
        if match2:
            return int(match2.group(1))
    return None


