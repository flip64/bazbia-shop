import os
import sys
import django

BASE_DIR = "/home/bazbiair/bazbia"
sys.path.insert(0, BASE_DIR)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "bazbia_shop.settings"
)

django.setup()


from django.core.management.base import BaseCommand

from suppliers.services.reports.daily_price_report import DailyPriceReportService


class Command(BaseCommand):
    help = "ارسال گزارش روزانه تغییر قیمت تأمین‌کنندگان"

    def handle(self, *args, **options):
        service = DailyPriceReportService()
        service.run()
      
