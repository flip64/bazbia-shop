#!/bin/bash

# مسیر پروژه
PROJECT_DIR="/home/flip/project/bazbia/bazbia-shop"
VENV_DIR="$PROJECT_DIR"
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

cd "$PROJECT_DIR"

# فعال کردن محیط مجازی
source "$VENV_DIR/bin/activate"

# نام فایل لاگ با تاریخ و ساعت
LOG_FILE="$LOG_DIR/scraping_$(date +%Y%m%d_%H%M).log"

# اجرای کد پایتون
python3 <<EOF >> "$LOG_FILE" 2>&1
import os
import sys
import django
from datetime import datetime
from django.contrib.auth import get_user_model

# اضافه کردن مسیر پروژه به sys.path (جایی که manage.py هست)
sys.path.insert(0, "$PROJECT_DIR")

# ست کردن تنظیمات Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bazbia.settings")
django.setup()

from scrap_abdisite.utils.fetche_product_list import fetche_products_list
from scrap_abdisite.utils.scrap_abdi_site import process_latest_file
from scrap_abdisite.utils.create_product import import_products_from_json

print("شروع Scraping:", datetime.now())

products, raw_file = fetche_products_list()
print(f"مرحله 1: Fetch products - {len(products)} محصول دریافت شد از {raw_file}")

processed = process_latest_file()
print(f"مرحله 2: Process latest file - {processed['products_count']} محصول پردازش شد")

User = get_user_model()
user = User.objects.first()
import_products_from_json(user)

print("پایان Scraping:", datetime.now())
EOF

echo "Scraping کامل شد. لاگ‌ها در $LOG_FILE ذخیره شدند."

