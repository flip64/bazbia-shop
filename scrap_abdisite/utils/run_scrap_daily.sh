#!/bin/bash
set -x

PROJECT_DIR="/home/bazbiair/bazbia"
LOG_DIR="$PROJECT_DIR/scrap_abdisite/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/daily_scraping_$(date +%Y%m%d).log"

echo "شروع Scraping روزانه:" $(date) >> "$LOG_FILE"

source /home/bazbiair/virtualenv/bazbia/3.10/bin/activate
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ محیط مجازی فعال نیست!" >> "$LOG_FILE"
    exit 1
else
    echo "✅ محیط مجازی فعال است: $VIRTUAL_ENV" >> "$LOG_FILE"
fi

cd "$PROJECT_DIR"
export PYTHONPATH="$PROJECT_DIR"

for script in \
     "$PROJECT_DIR/scrap_abdisite/utils/fetche_product_list.py" \
     "$PROJECT_DIR/scrap_abdisite/utils/scrap_abdi_site.py"
do
    python3 "$script" >> "$LOG_FILE" 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ $script با موفقیت اجرا شد" >> "$LOG_FILE"
    else
        echo "❌ خطا در اجرای $script" >> "$LOG_FILE"
    fi
done

echo "پایان Scraping روزانه:" $(date) >> "$LOG_FILE"