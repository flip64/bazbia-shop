# basalam_integration/management/commands/sync_basalam_categories.py

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import (
    BaseCommand,
    CommandError,
)
from django.db import transaction

from basalam_integration.models import BasalamCategory
from basalam_integration.services.client import (
    BasalamAPIError,
    BasalamClient,
)


class Command(BaseCommand):
    help = (
        "دریافت دسته‌های باسلام و ایجاد یا "
        "به‌روزرسانی آن‌ها در دیتابیس بازبیا"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help=(
                "نمایش نتیجه بدون ذخیره تغییرات "
                "در دیتابیس"
            ),
        )

        parser.add_argument(
            "--deactivate-missing",
            action="store_true",
            help=(
                "غیرفعال‌کردن دسته‌هایی که دیگر "
                "در پاسخ باسلام وجود ندارند"
            ),
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        deactivate_missing = options[
            "deactivate_missing"
        ]

        try:
            response = BasalamClient().get_categories()
        except (
            BasalamAPIError,
            ImproperlyConfigured,
        ) as exc:
            raise CommandError(str(exc)) from exc

        categories = response.get("data") or []

        if not isinstance(categories, list):
            raise CommandError(
                "ساختار پاسخ دسته‌بندی‌های باسلام معتبر نیست."
            )

        flattened_categories = []
        self.flatten_categories(
            categories=categories,
            result=flattened_categories,
            parent_title=None,
        )

        if not flattened_categories:
            raise CommandError(
                "هیچ دسته‌بندی از باسلام دریافت نشد."
            )

        created_count = 0
        updated_count = 0
        unchanged_count = 0
        skipped_count = 0
        received_ids = set()

        default_commission = Decimal(
            str(
                settings.BASALAM_DEFAULT_COMMISSION_PERCENT
            )
        )

        with transaction.atomic():
            for category_data in flattened_categories:
                category_id = category_data.get("id")
                title = category_data.get("title")

                if not category_id or not title:
                    skipped_count += 1
                    continue

                category_id = int(category_id)
                title = str(title).strip()

                received_ids.add(category_id)

                category = (
                    BasalamCategory.objects
                    .filter(
                        basalam_category_id=category_id
                    )
                    .first()
                )

                if category is None:
                    BasalamCategory.objects.create(
                        basalam_category_id=category_id,
                        title=title,
                        commission_percent=default_commission,
                        is_active=True,
                    )

                    created_count += 1
                    continue

                changed_fields = []

                if category.title != title:
                    category.title = title
                    changed_fields.append("title")

                if not category.is_active:
                    category.is_active = True
                    changed_fields.append("is_active")

                if changed_fields:
                    changed_fields.append("updated_at")

                    category.save(
                        update_fields=changed_fields
                    )

                    updated_count += 1
                else:
                    unchanged_count += 1

            deactivated_count = 0

            if deactivate_missing:
                missing_categories = (
                    BasalamCategory.objects
                    .filter(is_active=True)
                    .exclude(
                        basalam_category_id__in=received_ids
                    )
                )

                deactivated_count = (
                    missing_categories.update(
                        is_active=False
                    )
                )

            if dry_run:
                transaction.set_rollback(True)

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "حالت آزمایشی بود؛ هیچ تغییری ذخیره نشد."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "همگام‌سازی دسته‌های باسلام پایان یافت."
            )
        )

        self.stdout.write(
            f"دریافت‌شده: {len(flattened_categories)}"
        )
        self.stdout.write(
            f"ایجادشده: {created_count}"
        )
        self.stdout.write(
            f"به‌روزرسانی‌شده: {updated_count}"
        )
        self.stdout.write(
            f"بدون تغییر: {unchanged_count}"
        )
        self.stdout.write(
            f"ردشده: {skipped_count}"
        )
        self.stdout.write(
            f"غیرفعال‌شده: {deactivated_count}"
        )

        self.stdout.write(
            self.style.WARNING(
                "کارمزدهای موجود تغییر نکردند؛ "
                "دسته‌های جدید با کارمزد پیش‌فرض "
                f"{default_commission}٪ ساخته شدند."
            )
        )

    def flatten_categories(
        self,
        *,
        categories,
        result,
        parent_title,
    ):
        """
        تبدیل ساختار درختی دسته‌های باسلام به فهرست ساده.
        """

        for category in categories:
            if not isinstance(category, dict):
                continue

            category_id = category.get("id")
            title = category.get("title")

            if title and parent_title:
                display_title = (
                    f"{parent_title} ← {title}"
                )
            else:
                display_title = title

            result.append(
                {
                    "id": category_id,
                    "title": display_title,
                }
            )

            children = category.get("children") or []

            if children:
                self.flatten_categories(
                    categories=children,
                    result=result,
                    parent_title=display_title,
                  )
