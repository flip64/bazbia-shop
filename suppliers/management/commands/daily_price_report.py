from django.core.management.base import BaseCommand

from suppliers.services.reports.daily_price_report import DailyPriceReportService


class Command(BaseCommand):
    help = "ارسال گزارش روزانه تغییر قیمت تأمین‌کنندگان"

    def handle(self, *args, **options):
        service = DailyPriceReportService()
        service.run()
      
