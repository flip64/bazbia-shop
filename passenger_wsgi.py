import os
import sys

# 1. تنظیم مسیرهای پروژه
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)  # مسیر اصلی پروژه
sys.path.insert(1, os.path.join(BASE_DIR, 'bazbia'))  # مسیر اپلیکیشن اصلی

# 2. تنظیم متغیر محیطی
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bazbia_shop.settings')

# 3. راه اندازی WSGI
from django.core.wsgi import get_wsgi_application
try:
    application = get_wsgi_application()
except Exception as e:
    # ثبت خطا برای دیباگ
    with open(os.path.join(BASE_DIR, 'passenger_wsgi_error.log'), 'a') as f:
        f.write(f"WSGI Error: {str(e)}\n")
    raise