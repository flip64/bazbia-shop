import requests
from bs4 import BeautifulSoup
import json
import time
import os
from datetime import datetime, timedelta
from django.utils.text import slugify
import re

# مسیر app اصلی
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # میشه scrap_abdisite/
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)

headers = {"User-Agent": "Mozilla/5.0"}

list_cat = [
    "game-and-fun", "home-goods", "beauty-and-health",
    "digital-goods", "car-accessories", "sports-and-travel",
    "baby-and-infant", "fashion-and-clothing"
]

# پیدا کردن آخرین فایل
def get_last_file():
    files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith("raw_") and f.endswith(".json")]
    if not files:
        return None
    files.sort(key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)), reverse=True)
    return os.path.join(OUTPUT_DIR, files[0])

def is_need_scrap():
    last_file = get_last_file()
    if not last_file:
        return True  # هیچ فایلی نیست → باید اسکرپ کنیم

    last_time = datetime.fromtimestamp(os.path.getmtime(last_file))
    if datetime.now() - last_time > timedelta(hours=12):
        return True
    else:
        print(f"⏳ آخرین گزارش ({os.path.basename(last_file)}) کمتر از ۱۲ ساعت پیش ذخیره شده. نیازی به اسکرپ نیست.")
        return False

def fetche_productsـlist():
    """اسکرپ محصولات پخش عبدی یا خواندن آخرین فایل ذخیره‌شده"""
    products = []
    total_count = 0

    if not is_need_scrap():
        last_file = get_last_file()
        if last_file:
            with open(last_file, "r", encoding="utf-8") as f:
                products = json.load(f)
            return products, last_file
        else:
            return [], None

    for cat in list_cat:
        page = 1
        while True:
            url = f"https://pakhshabdi.com/product-category/{cat}/page/{page}/"
            print("=" * 60)
            print(f"📦 دسته‌بندی: {cat}")
            print(f"📄 در حال پردازش صفحه {page} از دسته {cat}...")
            print(f"🔗 URL: {url}")

            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code != 200:
                    print("❌ صفحه یافت نشد یا به پایان رسید.")
                    break
            except Exception as e:
                print(f"🚫 خطا در دریافت صفحه: {e}")
                break

            soup = BeautifulSoup(response.content, "html.parser")
            items = soup.find_all("li", class_="col-md-3 col-6 mini-product-con type-product")

            if not items:
                print("📭 هیچ محصولی در این صفحه یافت نشد. پایان این دسته.")
                break

            print(f"✅ {len(items)} محصول در صفحه {page} یافت شد.")
            no_price_in_row = 0

            for item in items:
                name_tag = item.find("h2", class_="product-title")
                name_link_tag = name_tag.find("a") if name_tag else None
                if not name_link_tag:
                    continue

                name = name_link_tag.text.strip()
                link = name_link_tag["href"] if name_link_tag.has_attr("href") else "لینک یافت نشد"
                slug = slugify(name)

                price_tag = item.find("span", class_="woocommerce-Price-amount")
                if not price_tag:
                    no_price_in_row += 1
                    if no_price_in_row >= 3:
                        break
                    continue
                else:
                    no_price_in_row = 0

                price_text = price_tag.text.strip()
                price_clean = re.sub(r"\D", "", price_text)
                try:
                    price = int(price_clean)
                except:
                    continue

                img_div = item.find("div", class_="img-con")
                img_tag = img_div.find("img") if img_div else None
                main_image = (
                    img_tag.get("src")
                    or img_tag.get("data-src")
                    or img_tag.get("data-lazy-src")
                    if img_tag else ""
                )

                desc_tag = item.find("div", class_="product-excerpt")
                description = desc_tag.text.strip() if desc_tag else ""

                products.append({
                    "id": None,
                    "name": name,
                    "slug": slug,
                    "description": description,
                    "checked_description": False,
                    "price": price,
                    "stock": None,
                    "category": cat,
                    "tags": [],
                    "checked_tags": False,
                    "specifications": [],
                    "checked_specs": False,
                    "features": [],
                    "images": [main_image] if main_image else [],
                    "checked_images": False,
                    "videos": [],
                    "product_link": link,
                    "variants": [],
                    "has_variants": False
                })

                total_count += 1
                print(f"➕ '{name}' اضافه شد. مجموع محصولات: {total_count}")

            if no_price_in_row >= 3:
                break

            page += 1
            time.sleep(1)

    # ذخیره فایل
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"raw_{timestamp}_{total_count}.json"
    file_path = os.path.join(OUTPUT_DIR, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print("=" * 60)
    print(f"✅ فایل «{file_path}» با {total_count} محصول ذخیره شد.")
    return products, file_path
