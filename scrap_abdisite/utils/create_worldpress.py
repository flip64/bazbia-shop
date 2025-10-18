# -*- coding: utf-8 -*-
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


# ---------- توابع کمکی ----------
category_cache = {}
tag_cache = {}

def get_or_create_category(slug, name):
    if slug in category_cache:
        return category_cache[slug]
    
    try:
        response = requests.get(url_categories, auth=(consumer_key, consumer_secret), params={"slug": slug})
        response.raise_for_status()
        data = response.json()
        
        if data:
            category_cache[slug] = data[0]['id']
            return data[0]['id']
            
        payload = {"name": name, "slug": slug}
        resp_create = requests.post(url_categories, auth=(consumer_key, consumer_secret), json=payload)
        resp_create.raise_for_status()
        
        category_id = resp_create.json()['id']
        category_cache[slug] = category_id
        print(f"دسته‌بندی '{name}' ساخته شد.")
        return category_id
        
    except requests.exceptions.RequestException as e:
        print(f"خطا در ساخت یا دریافت دسته‌بندی '{name}': {e}")
        return None

def get_or_create_tag(name):
    if name in tag_cache:
        return tag_cache[name]
    
    try:
        response = requests.get(url_tags, auth=(consumer_key, consumer_secret), params={"search": name})
        response.raise_for_status()
        data = response.json()
        
        if data:
            tag_cache[name] = data[0]['id']
            return data[0]['id']
            
        payload = {"name": name}
        resp_create = requests.post(url_tags, auth=(consumer_key, consumer_secret), json=payload)
        resp_create.raise_for_status()
        
        tag_id = resp_create.json()['id']
        tag_cache[name] = tag_id
        print(f"تگ '{name}' ساخته شد.")
        return tag_id
        
    except requests.exceptions.RequestException as e:
        print(f"خطا در ساخت یا دریافت تگ '{name}': {e}")
        return None

def get_all_products():
    products = {}
    page = 1
    while True:
        try:
            response = requests.get(url_products, auth=(consumer_key, consumer_secret), 
                                  params={"per_page": 100, "page": page})
            response.raise_for_status()
            data = response.json()
            
            if not data:
                break
                
            for p in data:
                products[p['slug']] = p
            page += 1
            
        except requests.exceptions.RequestException as e:
            print(f"خطا در دریافت محصولات: {e}")
            break
            
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
    
    if not slug:
        print(f"رد کردن محصول '{name}' به دلیل نداشتن slug.")
        continue
    
    # دسته‌بندی
    category_slug = product.get("category", "uncategorized")
    tags_list = product.get("tags", [])
    category_name = tags_list[0] if tags_list else category_slug
    category_id = get_or_create_category(category_slug, category_name)
    
    if category_id is None:
        print(f"رد کردن محصول '{name}' به دلیل مشکل دسته‌بندی.")
        continue

    # تگ‌ها
    tag_ids = []
    for tag_name in product.get("tags", []):
        if tag_name:  # بررسی وجود مقدار
            tag_id = get_or_create_tag(tag_name)
            if tag_id:
                tag_ids.append({"id": tag_id})

    # ویژگی‌ها
    attributes = []
    for spec in product.get("specifications", []):
        if spec and ":" in spec:
            attr_name = spec.split(":")[0].strip()
            attr_value = spec.split(":", 1)[1].strip()
            attributes.append({
                "name": attr_name,
                "options": [attr_value],
                "visible": True,
                "variation": False
            })
    
    for feature in product.get("features", []):
        if feature and ":" in feature:
            attr_name = feature.split(":")[0].strip()
            attr_value = feature.split(":", 1)[1].strip()
            attributes.append({
                "name": attr_name,
                "options": [attr_value],
                "visible": True,
                "variation": False
            })

    # داده محصول
    product_data = {
        "name": name,
        "slug": slug,
        "type": "simple",
        "regular_price": str(product.get("price", 0)),
        "description": product.get("description", ""),
        "short_description": product.get("short_description", ""),
        "categories": [{"id": category_id}],
        "tags": tag_ids,
        "attributes": attributes,
        "images": [{"src": img} for img in product.get("images", []) if img]
    }

    # مدیریت موجودی
    quantity = product.get("quantity")
    if quantity is not None:
        product_data["manage_stock"] = True
        product_data["stock_quantity"] = quantity
    else:
        product_data["manage_stock"] = False
        product_data["stock_status"] = "instock"

    # متادیتا
    if product.get("product_link"):
        product_data["meta_data"] = [{"key": "original_link", "value": product["product_link"]}]

    # بررسی وجود محصول و بروزرسانی یا اضافه کردن
    if slug in existing_products:
        existing_id = existing_products[slug]['id']
        existing_price = existing_products[slug].get('regular_price', "")
        existing_stock = existing_products[slug].get('stock_quantity')

        price_changed = str(product.get("price", 0)) != str(existing_price)
        stock_changed = quantity != existing_stock

        if price_changed or stock_changed:
            try:
                response = requests.put(f"{url_products}/{existing_id}", 
                                      auth=(consumer_key, consumer_secret), 
                                      json=product_data)
                response.raise_for_status()
                status = "updated"
                print(f"محصول '{name}' بروزرسانی شد.")
            except requests.exceptions.RequestException as e:
                status = "error"
                print(f"خطا در بروزرسانی '{name}': {e}")
        else:
            status = "no_change"
            print(f"محصول '{name}' تغییری نکرد، بروزرسانی لازم نیست.")
            
        log_rows.append({
            "slug": slug,
            "name": name,
            "old_price": existing_price,
            "new_price": product.get("price", 0),
            "old_stock": existing_stock,
            "new_stock": quantity,
            "status": status
        })
    else:
        try:
            response = requests.post(url_products, 
                                   auth=(consumer_key, consumer_secret), 
                                   json=product_data)
            response.raise_for_status()
            status = "added"
            print(f"محصول '{name}' اضافه شد!")
        except requests.exceptions.RequestException as e:
            status = "error"
            print(f"خطا در اضافه کردن '{name}': {e}")
            
        log_rows.append({
            "slug": slug,
            "name": name,
            "old_price": "",
            "new_price": product.get("price", 0),
            "old_stock": "",
            "new_stock": quantity,
            "status": status
        })

# ---------- نوشتن لاگ ----------
if log_rows:
    try:
        with open(log_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=log_fields)
            writer.writeheader()
            writer.writerows(log_rows)
        print(f"لاگ پردازش در فایل {log_file} ذخیره شد.")
    except Exception as e:
        print(f"خطا در نوشتن فایل لاگ: {e}")
else:
    print("هیچ داده‌ای برای ذخیره در لاگ وجود ندارد.")

print("پردازش محصولات کامل شد.")
