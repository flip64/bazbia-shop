# Generated by Django 5.2.4 on 2025-07-11 04:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='productvariant',
            name='expiration_date',
            field=models.DateField(blank=True, help_text='تاریخ انقضای محصول', null=True),
        ),
        migrations.AddField(
            model_name='productvariant',
            name='low_stock_threshold',
            field=models.PositiveIntegerField(default=5, help_text='آستانه هشدار اتمام موجودی برای این واریانت'),
        ),
    ]
