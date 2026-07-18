# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from suppliers.models import SupplierOffer
from suppliers.services.variant_price_sync import (
    sync_variant_price_from_offer,
)


class Command(BaseCommand):
    help = "بروزرسانی قیمت تمام واریانت‌ها بر اساس SupplierOfferها"

    def handle(self, *args, **options):
        offers = (
            SupplierOffer.objects
            .select_related("variant", "supplier")
            .all()
        )

        total_count = offers.count()
        updated_count = 0
        unchanged_count = 0
        error_count = 0

        self.stdout.write(
            f"شروع بروزرسانی قیمت {total_count} پیشنهاد تأمین‌کننده..."
        )

        for offer in offers.iterator(chunk_size=500):
            try:
                was_updated = sync_variant_price_from_offer(offer)

                if was_updated:
                    updated_count += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"بروزرسانی شد: "
                            f"Offer={offer.pk} | "
                            f"Variant={offer.variant_id}"
                        )
                    )
                else:
                    unchanged_count += 1

            except Exception as exc:
                error_count += 1

                self.stderr.write(
                    self.style.ERROR(
                        f"خطا: "
                        f"Offer={offer.pk} | "
                        f"Variant={offer.variant_id} | "
                        f"{exc}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "عملیات بروزرسانی قیمت‌ها تمام شد."
            )
        )

        self.stdout.write(f"تعداد کل: {total_count}")
        self.stdout.write(f"بروزرسانی‌شده: {updated_count}")
        self.stdout.write(f"بدون تغییر: {unchanged_count}")
        self.stdout.write(f"خطادار: {error_count}")
