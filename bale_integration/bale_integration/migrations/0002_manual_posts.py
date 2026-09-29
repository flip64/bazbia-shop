from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [("bale_integration", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="baleproductpost",
            name="publication_date",
            field=models.DateField(
                default=django.utils.timezone.localdate,
                verbose_name="تاریخ انتشار",
            ),
        ),
        migrations.AddField(
            model_name="baleproductpost",
            name="trigger",
            field=models.CharField(
                choices=[("cron", "ارسال تصادفی کرون"), ("manual", "ارسال دستی")],
                default="cron",
                max_length=10,
                verbose_name="روش ارسال",
            ),
        ),
        migrations.AddField(
            model_name="baleproductpost",
            name="cron_date",
            field=models.DateField(
                blank=True,
                null=True,
                verbose_name="تاریخ اجرای کرون",
            ),
        ),
        migrations.RunSQL(
            sql="UPDATE bale_integration_baleproductpost SET cron_date = publication_date",
            reverse_sql="UPDATE bale_integration_baleproductpost SET cron_date = NULL",
        ),
        migrations.AlterField(
            model_name="baleproductpost",
            name="cron_date",
            field=models.DateField(
                blank=True,
                null=True,
                unique=True,
                verbose_name="تاریخ اجرای کرون",
            ),
        ),
    ]
