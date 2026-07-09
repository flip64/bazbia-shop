from datetime import timedelta
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from suppliers.models import SupplierPriceHistory
from django.utils import timezone

import jdatetime







class DailyPriceReportService:

    def run(self):
        """
        اجرای کامل گزارش روزانه
        """

        changes = self.get_changes()

        if not changes:
            print("هیچ تغییر قیمتی در ۲۴ ساعت گذشته ثبت نشده است.")
            return False

        html = self.render(changes)

        self.send_email(html)

        print(f"گزارش با موفقیت ارسال شد. ({len(changes)} تغییر)")

        return True

    def get_changes(self):
        """
        تغییرات ۲۴ ساعت گذشته را برمی‌گرداند.
        """

        since = timezone.now() - timedelta(hours=24)

        history = (
            SupplierPriceHistory.objects
            .filter(created_at__gte=since)
            .select_related(
                "supplier_offer__supplier",
                "supplier_offer__variant__product",
            )
            .order_by("-created_at")
        )

        changes = []

        for item in history:

            previous = (
                SupplierPriceHistory.objects
                .filter(
                    supplier_offer=item.supplier_offer,
                    created_at__lt=item.created_at,
                )
                .order_by("-created_at")
                .first()
            )

            changes.append({
                "product": item.supplier_offer.variant.product.name,
                "sku": item.supplier_offer.variant.sku,
                "supplier": item.supplier_offer.supplier.name,
                "old_price": previous.price if previous else None,
                "new_price": item.price,
                "time": timezone.localtime(item.created_at),
            })

        return changes

    def render(self, changes):
        """
        رندر قالب HTML
        """
        now = timezone.localtime()

        return render_to_string(
            "suppliers/daily_price_report.html",
            {
                "report_date": jdatetime.datetime.fromgregorian(datetime=now).strftime("%Y/%m/%d %H:%M") ,
                "changes": changes,
                "count": len(changes),
            },
        )

    def send_email(self, html):
        """
        ارسال ایمیل گزارش
        """

        msg = EmailMultiAlternatives(
            subject="گزارش روزانه تغییر قیمت تأمین‌کنندگان",
            body="این گزارش به صورت HTML ارسال شده است.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[
                "jr64.naderloo@gmail.com",   # ایمیل خودت
            ],
        )

        msg.attach_alternative(html, "text/html")

        msg.send()