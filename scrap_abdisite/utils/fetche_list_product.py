import requests
from bs4 import BeautifulSoup
import json
import time
import os
from datetime import datetime
from slugify import slugify  # pip install python-slugify

products = []
total_count = 0  # شمارنده کل محصولات

list_cat = [
    "game-and-fun", "home-goods", "beauty-and-health",
    "digital-goods", "car-accessories", "sports-and-travel",
    "baby-and-infant", "fashion-and-clothing"
]

headers = {"User-Agent": "Mozilla/5.0"}

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

        no_price_in_row = 0  # شمارنده محصولات بدون قیمت پشت سر هم

        for item in items:
            name_tag = item.find("h2", class_="product-title")
            name_link_tag = name_tag.find("a") if name_tag else None
            if not name_link_tag:
                print("❗ نام محصول یافت نشد → رد شد.")
                continue

            name = name_link_tag.text.strip()
            link = name_link_tag["href"] if name_link_tag.has_attr("href") else "لینک یافت نشد"
            slug = slugify(name)

            price_tag = item.find("span", class_="woocommerce-Price-amount")
            if not price_tag:
                no_price_in_row += 1
                print(f"⛔ محصول بدون قیمت: '{name}'  ❗ (رد شد) ← ({no_price_in_row} پشت سر هم)")
                if no_price_in_row >= 3:
                    print("⚠️ سه محصول متوالی بدون قیمت → پایان این دسته.")
                    break
                continue
            else:
                no_price_in_row = 0  # ریست شمارنده اگر قیمت پیدا شد

            price_text = price_tag.text.strip()
            price_clean = price_text.replace("تومان", "").replace(",", "").strip()
            try:
                price = int(price_clean)
            except:
                print(f"❗ خطا در تبدیل قیمت برای '{name}' → رد شد.")
                continue

            img_div = item.find("div", class_="img-con")
            img_tag = img_div.find("img") if img_div else None
            main_image = img_tag.get("src") or img_tag.get("data-src") if img_tag else ""

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
            break  # اگر سه محصول پشت سر هم بدون قیمت بودند، دسته بعدی را شروع کن

        page += 1
        time.sleep(1)



# ساخت پوشه برای ذخیره فایل‌ها
output_dir = os.path.join(os.path.dirname(__file__), "../data/raw")
os.makedirs(output_dir, exist_ok=True)


# فرمت نام فایل با تاریخ و ساعت
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
filename = f"raw_{timestamp}_{total_count}.json"

# مسیر کامل فایل
file_path = os.path.join(output_dir, filename)

# ذخیره فایل
with open(file_path, "w", encoding="utf-8") as f:
    json.dump(products, f, ensure_ascii=False, indent=2)

print("=" * 60)
print(f"✅ فایل «{file_path}» با {total_count} محصول ذخیره شد.")
