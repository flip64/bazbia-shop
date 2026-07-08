from datetime import timedelta

from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

from suppliers.models import SupplierPriceHistory


class DailyPriceReportService:

    def run(self):
        """
        اجرای کامل گزارش روزانه
        """
        changes = self.get_changes()
        html = self.render(changes)
        self.send_email(html)

    def get_changes(self):
        """
        تغییرات 24 ساعت گذشته را برمی‌گرداند.
        """
        pass

    def render(self, changes):
        """
        قالب HTML را رندر می‌کند.
        """
        pass

    def send_email(self, html):
        """
        ایمیل گزارش را ارسال می‌کند.
        """
        pass
