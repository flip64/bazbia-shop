#!/bin/bash

# مسیر جاری اسکریپت (scrap_abdisite/utils)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# مسیر شاخه اصلی پروژه (bazbia-shop)
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# فولدر لاگ داخل scrap_abdisite
LOG_DIR="$PROJECT_DIR/scrap_abdisite/logs"
mkdir -p "$LOG_DIR"

# نام فایل لاگ با تاریخ و ساعت
LOG_FILE="$LOG_DIR/scraping_$(date +%Y%m%d_%H%M).log"

echo "شروع Scraping:" $(date) >> "$LOG_FILE"

# رفتن به شاخه اصلی پروژه
cd "$PROJECT_DIR"

# فعال‌سازی محیط مجازی (bin داخل پوشه اصلی)
if [ -f "$PROJECT_DIR/bin/activate" ]; then
    source "$PROJECT_DIR/bin/activate"
else
    echo "⚠️ محیط مجازی پیدا نشد!" >> "$LOG_FILE"
fi

# لاگ وضعیت محیط مجازی
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ محیط مجازی فعال نیست" >> "$LOG_FILE"
else
    echo "✅ محیط مجازی فعال است: $VIRTUAL_ENV" >> "$LOG_FILE"
fi

# چک کردن پایتون فعال
which python3 >> "$LOG_FILE"


# اجرای فایل‌ها به صورت ماژول Python
python3 -m scrap_abdisite.utils.fetche_products_list >> "$LOG_FILE" 2>&1
echo "فایل fetche_products_list.py اجرا شد" >> "$LOG_FILE"

python3 -m scrap_abdisite.utils.scrap_abdi_site >> "$LOG_FILE" 2>&1
echo "فایل scrap_abdi_site.py اجرا شد" >> "$LOG_FILE"

echo "پایان Scraping:" $(date) >> "$LOG_FILE"
echo "لاگ‌ها در $LOG_FILE ذخیره شدند."
