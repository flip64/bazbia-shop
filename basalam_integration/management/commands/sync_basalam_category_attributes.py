from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from basalam_integration.models import (
    BasalamCategory,
    BasalamCategoryAttributeSnapshot,
)
from basalam_integration.services.attribute_service import (
    get_mapped_basalam_categories,
    sync_category_attributes,
)
from basalam_integration.services.client import (
    BasalamAPIError,
    BasalamClient,
)


class Command(BaseCommand):
    help = (
        "دریافت ویژگی‌های دسته‌های نگاشت‌شده "
        "باسلام و ذخیره پاسخ کامل API"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--category-id",
            type=int,
            action="append",
            dest="category_ids",
            help=(
                "شناسه دسته باسلام؛ "
                "برای چند دسته می‌توان گزینه را تکرار کرد."
            ),
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help=(
                "دریافت و بررسی پاسخ بدون "
                "ذخیره در دیتابیس"
            ),
        )

    def handle(self, *args, **options):
        category_ids = options.get(
            "category_ids"
        ) or []

        dry_run = options["dry_run"]

        if category_ids:
            categories = (
                BasalamCategory.objects
                .filter(
                    basalam_category_id__in=category_ids,
                    is_active=True,
                )
                .order_by("title")
            )
        else:
            categories = (
                get_mapped_basalam_categories()
            )

        categories = list(categories)

        if not categories:
            raise CommandError(
                "هیچ دسته فعالی برای دریافت "
                "ویژگی‌ها پیدا نشد."
            )

        client = BasalamClient()

        success_count = 0
        failed_count = 0
        total_attributes = 0

        for category in categories:
            try:
                result = sync_category_attributes(
                    category,
                    client=client,
                    save=not dry_run,
                )
            except BasalamAPIError as exc:
                failed_count += 1

                if not dry_run:
                    snapshot, _ = (
                        BasalamCategoryAttributeSnapshot
                        .objects
                        .get_or_create(
                            basalam_category=category,
                        )
                    )

                    snapshot.last_error = str(exc)

                    snapshot.save(
                        update_fields=[
                            "last_error",
                            "fetched_at",
                        ]
                    )

                self.stderr.write(
                    self.style.ERROR(
                        f"خطا در دسته "
                        f"{category.basalam_category_id} "
                        f"- {category.title}: {exc}"
                    )
                )

                continue

            success_count += 1
            total_attributes += (
                result.attributes_count
            )

            save_status = (
                "بررسی شد"
                if dry_run
                else "ذخیره شد"
            )

            self.stdout.write(
                f"{result.category_id} - "
                f"{result.title}: "
                f"{result.attributes_count} ویژگی "
                f"({save_status})"
            )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "حالت آزمایشی بود؛ "
                    "اطلاعاتی ذخیره نشد."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "همگام‌سازی ویژگی‌ها پایان یافت."
            )
        )

        self.stdout.write(
            f"دسته‌های موفق: {success_count}"
        )

        self.stdout.write(
            f"دسته‌های ناموفق: {failed_count}"
        )

        self.stdout.write(
            f"مجموع ویژگی‌های دریافت‌شده: "
            f"{total_attributes}"
          )
