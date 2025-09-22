#!/bin/bash
set -x

PROJECT_DIR="/home/bazbiair/bazbia"
LOG_DIR="$PROJECT_DIR/scrap_abdisite/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/create_product_$(date +%Y%m%d_%H).log"

echo "شروع اجرای create_product.py:" $(date) >> "$LOG_FILE"

source /home/bazbiair/virtualenv/bazbia/3.10/bin/activate
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ محیط مجازی فعال نیست!" >> "$LOG_FILE"
    exit 1
else
    echo "✅ محیط مجازی فعال است: $VIRTUAL_ENV" >> "$LOG_FILE"
fi

cd "$PROJECT_DIR"
export PYTHONPATH="$PROJECT_DIR"

python3 "$PROJECT_DIR/scrap_abdisite/utils/create_product.py" >> "$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ create_product.py با موفقیت اجرا شد" >> "$LOG_FILE"
else
    echo "❌ خطا در اجرای create_product.py" >> "$LOG_FILE"
fi

echo "پایان اجرای create_product.py:" $(date) >> "$LOG_FILE"