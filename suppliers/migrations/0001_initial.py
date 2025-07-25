# Generated by Django 5.2.4 on 2025-07-15 21:00

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='نام تأمین\u200cکننده')),
                ('website', models.URLField(blank=True, null=True, verbose_name='آدرس وب\u200cسایت')),
                ('phone', models.CharField(blank=True, max_length=50, null=True, verbose_name='شماره تماس')),
                ('email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='ایمیل')),
                ('address', models.TextField(blank=True, null=True, verbose_name='آدرس')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')),
            ],
            options={
                'verbose_name': 'تأمین\u200cکننده',
                'verbose_name_plural': 'تأمین\u200cکنندگان',
                'ordering': ['name'],
            },
        ),
    ]
