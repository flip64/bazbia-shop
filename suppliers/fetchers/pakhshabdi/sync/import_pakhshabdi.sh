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
python suppliers/fetchers/pakhshabdi/sync/import_pakhshabdi.py

EXIT_CODE=$?

echo "پایان: $(date)"
echo "Exit Code: $EXIT_CODE"
echo "====================================="

exit $EXIT_CODE
