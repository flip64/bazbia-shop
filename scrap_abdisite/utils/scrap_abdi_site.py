
# scrap_abdisite/utils/scrap_abdi_site.py
import os
import json
from datetime import datetime
from scrap_abdisite.utils.abdi_fetcher import extract_specifications

is_running = False


INPUT_FOLDER = "abdi_products_versions"
OUTPUT_FOLDER = "abdi_products_versions_edited"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def process_latest_file():
    # پیدا کردن آخرین فایل
    files = [f for f in os.listdir(INPUT_FOLDER) if f.startswith("bazbia_products_") and f.endswith(".json")]
    if not files:
        raise FileNotFoundError("هیچ فایل JSON معتبری پیدا نشد.")

    def file_datetime(f):
        parts = f.split("_")
        if len(parts) < 4:
            return datetime.min
        date_part = parts[2]
        time_part = parts[3]
        try:
            return datetime.strptime(date_part + time_part, "%Y%m%d%H%M")
        except ValueError:
            return datetime.min

    files.sort(key=file_datetime, reverse=True)
    latest_file = files[0]
    file_path = os.path.join(INPUT_FOLDER, latest_file)



    
    # خواندن و پردازش
    with open(file_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    for product in products:
        # مثال: استخراج مشخصات اگر لینک داشت
        if "product_link" in product:
            try:
                product["specifications"] = extract_specifications(product["product_link"])
            except Exception:
                product["specifications"] = []




    
    # ذخیره فایل ویرایش شده
    timestamp = datetime.now().strftime("%Y%m%d_%H%M_%f")[:-3]
    new_filename = latest_file.replace(".json", f"_edited_{timestamp}.json")
    output_path = os.path.join(OUTPUT_FOLDER, new_filename)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    return {"latest_file": latest_file, "edited_file": new_filename, "products_count": len(products)}
