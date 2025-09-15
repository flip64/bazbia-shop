#!/bin/bash
set -x  # برای نمایش دستورات اجرا شده

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

LOG_DIR="$PROJECT_DIR/scrap_abdisite/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/scraping_$(date +%Y%m%d_%H%M).log"

echo "شروع Scraping:" $(date) >> "$LOG_FILE"

cd "$PROJECT_DIR"
export PYTHONPATH="$PROJECT_DIR"

# فعال‌سازی محیط مجازی
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

which python3 >> "$LOG_FILE"

# اجرای مستقیم فایل Python
python3 scrap_abdisite/utils/fetche_products_list.py >> "$LOG_FILE" 2>&1
echo "فایل fetche_products_list.py اجرا شد" >> "$LOG_FILE"

python3 scrap_abdisite/utils/scrap_abdi_site.py >> "$LOG_FILE" 2>&1
echo "فایل scrap_abdi_site.py اجرا شد" >> "$LOG_FILE"

echo "پایان Scraping:" $(date) >> "$LOG_FILE"
