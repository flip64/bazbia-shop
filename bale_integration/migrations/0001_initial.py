from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True
    dependencies = [("products", "0011_remove_product_quantity")]
    operations = [
        migrations.CreateModel(
            name="BaleProductPost",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "publication_date",
                    models.DateField(
                        default=django.utils.timezone.localdate,
                        unique=True,
                        verbose_name="تاریخ انتشار",
                    ),
                ),
                ("channel_id", models.CharField(max_length=255, verbose_name="کانال")),
                ("message_id", models.BigIntegerField(blank=True, null=True, verbose_name="شناسه پیام")),
                ("is_successful", models.BooleanField(default=False, verbose_name="ارسال موفق")),
                ("attempt_count", models.PositiveIntegerField(default=0, verbose_name="تعداد تلاش")),
                ("error_message", models.TextField(blank=True, verbose_name="متن خطا")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="ایجاد")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="آخرین تغییر")),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="bale_posts",
                        to="products.product",
                        verbose_name="محصول",
                    ),
                ),
            ],
            options={
                "verbose_name": "انتشار محصول در بله",
                "verbose_name_plural": "انتشار محصولات در بله",
                "ordering": ("-publication_date", "-created_at"),
            },
        )
    ]
