import requests
import json
import os
import glob
import csv
from datetime import datetime

# ---------- مسیرهای نسبی ----------
script_dir = os.path.dirname(__file__)  # مسیر اسکریپت فعلی

# JSON ها: یک پوشه عقب -> data/edited
folder_path = os.path.abspath(os.path.join(script_dir, "..", "data", "edited"))

# لاگ‌ها: یک پوشه عقب -> data/logs
log_folder = os.path.abspath(os.path.join(script_dir, "..", "logs"))
os.makedirs(log_folder, exist_ok=True)

print("مسیر پوشه JSON ها:", folder_path)
print("مسیر پوشه لاگ:", log_folder)

# ---------- اطلاعات API ووکامرس ----------
url_products = "https://bazbia.ir/wp-json/wc/v3/products"
url_categories = "https://bazbia.ir/wp-json/wc/v3/products/categories"
url_tags = "https://bazbia.ir/wp-json/wc/v3/products/tags"
consumer_key = "ck_803298f060530d6afe5f9beff0dd9bd097549ee7"
consumer_secret = "cs_cc2026350c028fe1b3a9204195ad963b37c4d265"

# ---------- پیدا کردن آخرین فایل ----------
files = glob.glob(os.path.join(folder_path, "edited_*.json"))
if not files:
    print("هیچ فایل JSON پیدا نشد!")
    exit()

files.sort()
latest_file = files[-1]
print("آخرین فایل پیدا شده:", latest_file)

with open(latest_file, "r", encoding="utf-8") as f:
    daily_products = json.load(f)

print(f"{len(daily_products)} محصول برای پردازش در فایل {latest_file} پیدا شد.")

# ---------- توابع کمکی ----------
category_cache = {}
tag_cache = {}

def get_or_create_category(slug, name):
    if slug in category_cache:
        return category_cache[slug]
    response = requests.get(url_categories, auth=(consumer_key, consumer_secret), params={"slug": slug})
    data = response.json()
    if data:
        category_cache[slug] = data[0]['id']
        return data[0]['id']
    payload = {"name": name, "slug": slug}
    resp_create = requests.post(url_categories, auth=(consumer_key, consumer_secret), json=payload)
    if resp_create.status_code in [200, 201]:
        category_id = resp_create.json()['id']
        category_cache[slug] = category_id
        print(f"دسته‌بندی '{name}' ساخته شد.")
        return category_id
    else:
        print("خطا در ساخت دسته‌بندی:", resp_create.text)
        return None

def get_or_create_tag(name):
    if name in tag_cache:
        return tag_cache[name]
    response = requests.get(url_tags, auth=(consumer_key, consumer_secret), params={"search": name})
    data = response.json()
    if data:
        tag_cache[name] = data[0]['id']
        return data[0]['id']
    payload = {"name": name}
    resp_create = requests.post(url_tags, auth=(consumer_key, consumer_secret), json=payload)
    if resp_create.status_code in [200, 201]:
        tag_id = resp_create.json()['id']
        tag_cache[name] = tag_id
        print(f"تگ '{name}' ساخته شد.")
        return tag_id
    else:
        print("خطا در ساخت تگ:", resp_create.text)
        return None

def get_all_products():
    products = {}
    page = 1
    while True:
        response = requests.get(url_products, auth=(consumer_key, consumer_secret), params={"per_page": 100, "page": page})
        data = response.json()
        if not data:
            break
        for p in data:
            products[p['slug']] = p
        page += 1
    print(f"{len(products)} محصول موجود در ووکامرس دریافت شد.")
    return products

# ---------- آماده سازی لاگ ----------
log_file = os.path.join(log_folder, f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
log_fields = ["slug", "name", "old_price", "new_price", "old_stock", "new_stock", "status"]
log_rows = []

# ---------- پردازش محصولات ----------
existing_products = get_all_products()

for product in daily_products:
    slug = product.get("slug")
    name = product.get("name", "نام ندارد")
    
    # دسته‌بندی
    category_slug = product.get("category", "uncategorized")
    category_name = product.get("tags", [category_slug])[0]
    category_id = get_or_create_category(category_slug, category_name)
    if category_id is None:
        print(f"رد کردن محصول '{name}' به دلیل مشکل دسته‌بندی.")
        continue

    # تگ‌ها
    tag_ids = []
    for tag_name in product.get("tags", []):
        tag_id = get_or_create_tag(tag_name)
        if tag_id:
            tag_ids.append({"id": tag_id})

    # ویژگی‌ها
    attributes = []
    for spec in product.get("specifications", []):
        attributes.append({
            "name": spec.split(":")[0] if ":" in spec else "مشخصه",
            "options": [spec.split(":",1)[1].strip()] if ":" in spec else [spec],
            "visible": True,
            "variation": False
        })
    for feature in product.get("features", []):
        attributes.append({
            "name": feature.split(":")[0] if ":" in feature else "ویژگی",
            "options": [feature.split(":",1)[1].strip()] if ":" in feature else [feature],
            "visible": True,
            "variation": False
        })

    # داده محصول
    product_data = {
        "name": name,
        "type": "simple",
        "regular_price": str(product.get("price", 0)),
        "description": product.get("description", ""),
        "categories": [{"id": category_id}],
        "tags": tag_ids,
        "attributes": attributes,
        "images": [{"src": img} for img in product.get("images", [])]
    }

    if product.get("product_link"):
        product_data["meta_data"] = [{"key": "original_link", "value": product["product_link"]}]

    # بررسی وجود محصول و بروزرسانی یا اضافه کردن
    if slug in existing_products:
        existing_id = existing_products[slug]['id']
        existing_price = existing_products[slug].get('regular_price', "")
        existing_stock = existing_products[slug].get('stock_quantity', None)

        price_changed = str(product.get("price", 0)) != existing_price
        stock_changed = product.get("quantity") is not None and product.get("quantity") != existing_stock

        if price_changed or stock_changed:
            if product.get("quantity") is not None:
                product_data["stock_quantity"] = product["quantity"]
            response = requests.put(f"{url_products}/{existing_id}", auth=(consumer_key, consumer_secret), json=product_data)
            status = "updated" if response.status_code == 200 else "error"
            print(f"محصول '{name}' بروزرسانی شد." if status=="updated" else f"خطا در بروزرسانی '{name}': {response.text}")
        else:
            status = "no_change"
            print(f"محصول '{name}' تغییری نکرد، بروزرسانی لازم نیست.")
        log_rows.append({
            "slug": slug,
            "name": name,
            "old_price": existing_price,
            "new_price": product.get("price", 0),
            "old_stock": existing_stock,
            "new_stock": product.get("quantity"),
            "status": status
        })
    else:
        response = requests.post(url_products, auth=(consumer_key, consumer_secret), json=product_data)
        status = "added" if response.status_code == 201 else "error"
        print(f"محصول '{name}' اضافه شد!" if status=="added" else f"خطا در اضافه کردن '{name}': {response.text}")
        log_rows.append({
            "slug": slug,
            "name": name,
            "old_price": "",
            "new_price": product.get("price", 0),
            "old_stock": "",
            "new_stock": product.get("quantity"),
            "status": status
        })

# ---------- نوشتن لاگ ----------
with open(log_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=log_fields)
    writer.writeheader()
    writer.writerows(log_rows)

print(f"لاگ پردازش در فایل {log_file} ذخیره شد.")
