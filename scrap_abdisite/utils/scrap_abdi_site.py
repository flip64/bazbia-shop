# scrap_abdisite/utils/scrap_abdi_site.py

import os
import json
from datetime import datetime
from scrap_abdisite.utils.abdi_fetcher import extract_specifications, extract_tags, extract_product_images
from time import sleep
import logging

is_running = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # میشه scrap_abdisite/
RAW_FOLDER = os.path.join(BASE_DIR, "data/raw")
EDITED_FOLDER = os.path.join(BASE_DIR, "data/edited")
os.makedirs(EDITED_FOLDER, exist_ok=True)

# تنظیمات لاگ
LOG_FILE = os.path.join(EDITED_FOLDER, "scrap_log.txt")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)


def process_latest_file():
    result = merge_new_products()
    products = result['merged_products']

    processed = []
    batch_size = 20  # هر چند محصول یکبار ذخیره کن

    for idx, product in enumerate(products, start=1):
        if "product_link" in product and product["product_link"]:

            if not product.get("checked_specs", False):
                try:
                    new_specs = extract_specifications(product["product_link"])
                    product["specifications"].extend(new_specs)
                    product["checked_specs"] = True
                    logging.info(f"✅ مشخصات محصول '{product.get('name')}' استخراج شد.")
                except Exception as e:
                    logging.error(f"❌ خطا در استخراج مشخصات محصول {product.get('name')}: {e}")

            if not product.get("checked_tags", False):
                try:
                    new_tags = extract_tags(product["product_link"])
                    product["tags"].extend([t for t in new_tags if t not in product["tags"]])
                    product["checked_tags"] = True
                    logging.info(f"✅ تگ‌های محصول '{product.get('name')}' استخراج شد.")
                except Exception as e:
                    logging.error(f"❌ خطا در استخراج تگ محصول {product.get('name')}: {e}")

            if not product.get("checked_images", False):
                try:
                    new_images = extract_product_images(product["product_link"])
                    product.setdefault("images", [])
                    product["images"].extend([img for img in new_images if img not in product["images"]])
                    product["checked_images"] = True
                    logging.info(f"✅ تصاویر محصول '{product.get('name')}' استخراج شد.")
                except Exception as e:
                    logging.error(f"❌ خطا در استخراج تصاویر محصول {product.get('name')}: {e}")

            processed.append(product)

            # هر batch_size محصول یکبار ذخیره کن
            if idx % batch_size == 0:
                save_partial(processed, suffix="temp")
                logging.info(f"💾 ذخیره موقت بعد از {idx} محصول")

            sleep(1)

    # در پایان: ذخیره فایل کامل
    result_savefile = save_final(processed)
    clear_temp_files()
    return {
        "edited_file": "FINAL",
        "products_count": len(processed)
    }


def save_partial(products, suffix):
    clear_temp_files()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"edited_{timestamp}_{suffix}.json"
    output_path = os.path.join(EDITED_FOLDER, filename)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)


def save_final(products):
    try:
        os.makedirs(EDITED_FOLDER, exist_ok=True)  # مطمئن شو پوشه وجود داره
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        total_count = len(products)
        filename = f"edited_{timestamp}_{total_count}.json"
        output_path = os.path.join(EDITED_FOLDER, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        logging.info(f"💾 فایل نهایی ذخیره شد: {filename}")
        return True
    except Exception as e:
        logging.error(f"❌ خطا در ذخیره فایل نهایی: {e}")
        return False


def merge_new_products():
    # پیدا کردن آخرین فایل raw
    raw_files = [f for f in os.listdir(RAW_FOLDER) if f.startswith("raw_") and f.endswith(".json")]
    if not raw_files:
        raise FileNotFoundError("هیچ فایل خامی پیدا نشد.")

    raw_files.sort(reverse=True)
    latest_raw_file = raw_files[0]
    raw_path = os.path.join(RAW_FOLDER, latest_raw_file)

    # پیدا کردن فایل ویرایش شده روز قبل
    edited_files = [f for f in os.listdir(EDITED_FOLDER) if f.endswith(".json")]
    if not edited_files:
        previous_edited = None
    else:
        # مرتب سازی بر اساس تاریخ داخل نام فایل
        def extract_datetime(f):
            parts = f.split("_")
            if len(parts) < 4:
                return datetime.min
            date_part = parts[2]
            time_part = parts[3].split(".")[0]
            try:
                return datetime.strptime(date_part + time_part, "%Y%m%d%H%M")
            except:
                return datetime.min

        edited_files.sort(key=extract_datetime, reverse=True)
        previous_edited = edited_files[0]

    # بارگذاری فایل‌ها
    with open(raw_path, "r", encoding="utf-8") as f:
        raw_products = json.load(f)

    if previous_edited:
        prev_path = os.path.join(EDITED_FOLDER, previous_edited)
        with open(prev_path, "r", encoding="utf-8") as f:
            prev_products = json.load(f)
    else:
        prev_products = []

    # ساخت یک set از لینک ها برای تشخیص محصولات جدید
    prev_slugs = {p["product_link"] for p in prev_products}
    new_products = [p for p in raw_products if p["product_link"] not in prev_slugs]

    # اضافه کردن محصولات جدید به فایل روز قبل
    merged_products = prev_products + new_products

    logging.info(f"🆕 تعداد محصولات جدید: {len(new_products)}")
    logging.info(f"📦 مجموع محصولات پس از ادغام: {len(merged_products)}")

    return {
        "raw_file": latest_raw_file,
        "previous_edited_file": previous_edited,
        "new_products_count": len(new_products),
        "merged_products": merged_products
    }


def clear_temp_files():
    """حذف تمام فایل‌های موقت (_temp) از پوشه EDITED_FOLDER"""
    for f in os.listdir(EDITED_FOLDER):
        if f.startswith("edited_") and "_temp" in f:
            try:
                os.remove(os.path.join(EDITED_FOLDER, f))
                logging.info(f"🗑️ حذف فایل موقت: {f}")
            except Exception as e:
                logging.error(f"❌ خطا در حذف فایل موقت {f}: {e}")
