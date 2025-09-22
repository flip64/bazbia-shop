#!/bin/bash
set -x

# ---------- مسیر پروژه و لاگ ----------
PROJECT_DIR="/home/bazbiair/bazbia"
LOG_DIR="$PROJECT_DIR/scrap_abdisite/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/create_product_$(date +%Y%m%d_%H%M%S).log"

# ---------- شروع لاگ ----------
echo "شروع اجرای create_product.py:" $(date) >> "$LOG_FILE"

# ---------- فعال کردن محیط مجازی ----------
source /home/bazbiair/virtualenv/bazbia/3.10/bin/activate
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ محیط مجازی فعال نیست!" >> "$LOG_FILE"
    exit 1
else
    echo "✅ محیط مجازی فعال است: $VIRTUAL_ENV" >> "$LOG_FILE"
fi

# ---------- اجرای اسکریپت Python ----------
cd "$PROJECT_DIR"
export PYTHONPATH="$PROJECT_DIR"

python3 "$PROJECT_DIR/scrap_abdisite/utils/create_product.py" >> "$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ create_product.py با موفقیت اجرا شد" >> "$LOG_FILE"
else
    echo "❌ خطا در اجرای create_product.py" >> "$LOG_FILE"
fi

echo "پایان اجرای create_product.py:" $(date) >> "$LOG_FILE"

# ---------- ارسال ایمیل با Python SMTP ----------
STOP_FILE="$PROJECT_DIR/scrap_abdisite/stopemail"

if [ -f "$STOP_FILE" ]; then
    echo "⛔ ارسال ایمیل متوقف شد (فایل stopemail وجود دارد)" >> "$LOG_FILE"
    rm -f "$STOP_FILE"
    echo "🧹 فایل stopemail حذف شد" >> "$LOG_FILE"
else
    EMAIL_FROM="info@bazbia.ir"          # ایمیل هاست
    EMAIL_TO="hamberger.flip@gmail.com"  # ایمیل خودت
    SMTP_SERVER="mail.bazbia.ir"
    SMTP_PORT=587
    EMAIL_PASS="nima32641324"

    python3 <<EOF
import smtplib
from email.mime.text import MIMEText

with open("$LOG_FILE", "r", encoding="utf-8") as f:
    content = f.read()

msg = MIMEText(content)
msg["Subject"] = "گزارش create_product.py - $(date '+%Y-%m-%d %H:%M')"
msg["From"] = "$EMAIL_FROM"
msg["To"] = "$EMAIL_TO"

try:
    server = smtplib.SMTP("$SMTP_SERVER", $SMTP_PORT)
    server.starttls()
    server.login("$EMAIL_FROM", "$EMAIL_PASS")
    server.send_message(msg)
    server.quit()
    print("📧 فایل لاگ با موفقیت به ایمیل ارسال شد")
except Exception as e:
    print("❌ خطا در ارسال ایمیل:", e)
EOF
fi
