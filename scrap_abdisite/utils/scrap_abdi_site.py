import os
import json
from datetime import datetime
from scrap_abdisite.utils.abdi_fetcher import extract_specifications
# مسیرها
INPUT_FOLDER = "abdi_products_versions"
OUTPUT_FOLDER = "abdi_products_versions_edited"

# ایجاد پوشه خروجی در صورت عدم وجود
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def get_latest_file(folder):
    if not os.path.exists(folder):
        raise FileNotFoundError(f"پوشه ورودی پیدا نشد: {folder}")

    files = [f for f in os.listdir(folder) if f.startswith("bazbia_products_") and f.endswith(".json")]
    if not files:
        raise FileNotFoundError(f"هیچ فایل JSON معتبری در پوشه {folder} پیدا نشد.")

    def file_datetime(f):
        parts = f.split("_")
        if len(parts) < 4:
            return datetime.min  # فایل نامعتبر
        date_part = parts[2]  # مثال: 20250817
        time_part = parts[3]  # مثال: 1744
        try:
            return datetime.strptime(date_part + time_part, "%Y%m%d%H%M")
        except ValueError:
            return datetime.min

    files.sort(key=file_datetime, reverse=True)
    return files[0]

def process_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        products = json.load(f)  # مستقیم لیست محصولات

    print(f"تعداد محصولات: {len(products)}")
    for i, product in enumerate(products, start=1):
        print(f"{i}. {product.get('name', 'نامشخص')} - قیمت: {product.get('price', 'نامشخص')}")

    # اینجا می‌توانید پردازش واقعی اضافه کنید (مثلاً آپدیت قیمت، تگ‌ها و مشخصات)
    return products

def save_edited_file(products, original_filename):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M_%f")[:-3]
    new_filename = original_filename.replace(".json", f"_edited_{timestamp}.json")
    output_path = os.path.join(OUTPUT_FOLDER, new_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print(f"فایل ویرایش شده ذخیره شد: {output_path}")

def main():
    latest_file = get_latest_file(INPUT_FOLDER)
    print(f"آخرین فایل پیدا شد: {latest_file}")

    file_path = os.path.join(INPUT_FOLDER, latest_file)
    products = process_file(file_path)
    save_edited_file(products, latest_file)

if __name__ == "__main__":
    main()
