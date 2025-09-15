#!/bin/bash

# مسیر جاری اسکریپت (شاخه scrap_abdisite/utils)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# مسیر شاخه اصلی پروژه (یک سطح بالاتر از scrap_abdisite)
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# فولدر لاگ داخل شاخه scrap_abdisite
LOG_DIR="$PROJECT_DIR/scrap_abdisite/logs"
mkdir -p "$LOG_DIR"

# نام فایل لاگ با تاریخ و ساعت
LOG_FILE="$LOG_DIR/scraping_$(date +%Y%m%d_%H%M).log"

# اضافه کردن مسیر پروژه به PYTHONPATH تا پکیج scrap_abdisite پیدا شود
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

echo "شروع Scraping:" $(date) >> "$LOG_FILE"

# اجرای فایل اول
python3 "$PROJECT_DIR/scrap_abdisite/utils/fetche_products_list.py" >> "$LOG_FILE" 2>&1
echo "فایل fetche_products_list.py اجرا شد" >> "$LOG_FILE"

# اجرای فایل دوم
python3 "$PROJECT_DIR/scrap_abdisite/utils/scrap_abdi_site.py" >> "$LOG_FILE" 2>&1
echo "فایل scrap_abdi_site.py اجرا شد" >> "$LOG_FILE"

echo "پایان Scraping:" $(date) >> "$LOG_FILE"
echo "لاگ‌ها در $LOG_FILE ذخیره شدند."
