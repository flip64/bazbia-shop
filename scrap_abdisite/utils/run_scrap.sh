#!/bin/bash

# مسیر جاری اسکریپت (شاخه اسکریپت)
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

# نام فایل لاگ با تاریخ و ساعت
LOG_FILE="$LOG_DIR/scraping_$(date +%Y%m%d_%H%M).log"

echo "شروع Scraping:" $(date) >> "$LOG_FILE"

# اجرای فایل اول
python3 "$PROJECT_DIR/fetche_products_list.py" >> "$LOG_FILE" 2>&1
echo "فایل fetche_products_list.py اجرا شد" >> "$LOG_FILE"

# اجرای فایل دوم
python3 "$PROJECT_DIR/scrap_abdi_site.py" >> "$LOG_FILE" 2>&1
echo "فایل scrap_abdi_site.py اجرا شد" >> "$LOG_FILE"

echo "پایان Scraping:" $(date) >> "$LOG_FILE"
