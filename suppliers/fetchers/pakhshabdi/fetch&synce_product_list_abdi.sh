#!/bin/bash

# فعال کردن محیط مجازی
source /home/bazbiair/virtualenv/bazbia/3.10/bin/activate

# رفتن به پوشه پروژه
cd /home/bazbiair/bazbia || exit 1

echo "====================================="
echo "شروع: $(date)"
echo "Python: $(which python)"
echo "Version: $(python --version)"

# اجرای اسکریپت
echo "شروع: scrap list"
python suppliers/fetchers/pakhshabdi/fetch_product_list.py
echo "پایان : scrap list"
echo "شروع: همگام سازی لیست "

python suppliers/fetchers/pakhshabdi/sync_product_abdi.py

echo "پایان  همگام سازی لیست "
EXIT_CODE=$?

echo "پایان: $(date)"
echo "Exit Code: $EXIT_CODE"
echo "====================================="

exit $EXIT_CODE
