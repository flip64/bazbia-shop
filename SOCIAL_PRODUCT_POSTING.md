# انتشار محصول در بله و تلگرام

## متغیرهای محیطی

```env
BALE_BOT_TOKEN=...
BALE_CHANNEL_ID=@bazbia
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHANNEL_ID=@your_telegram_channel
```

ربات هر شبکه باید مدیر کانال خودش باشد و اجازه ارسال پیام داشته باشد.

## آماده‌سازی دیتابیس

```bash
python manage.py migrate
```

## آزمایش اتصال

```bash
python manage.py test_bale_channel
python manage.py test_telegram_channel
```

این دو دستور یک پیام آزمایشی واقعی در کانال منتشر می‌کنند.

## ارسال تصادفی مخصوص کرون

```bash
python manage.py send_daily_product --exclude-days 30
python manage.py send_daily_telegram_product --exclude-days 30
```

هر دستور در شبکه خودش محصولی را که در ۳۰ روز گذشته توسط کرون همان شبکه
ارسال شده باشد، دوباره انتخاب نمی‌کند. ارسال دستی در این محدودیت محاسبه نمی‌شود.

## ارسال دستی با شناسه محصول

```bash
python manage.py send_bale_product --product-id 123
python manage.py send_telegram_product --product-id 123
```

ارسال دستی محدودیت زمانی ندارد. برای پیش‌نمایش بدون ارسال واقعی، گزینه
`--dry-run` را به انتهای دستور اضافه کنید.

## نمونه کرون cPanel

```cron
15 10 * * * /home/bazbiair/virtualenv/bazbia/3.10/bin/python /home/bazbiair/bazbia/manage.py send_daily_product --exclude-days 30 >> /home/bazbiair/logs/bale_products.log 2>&1
30 10 * * * /home/bazbiair/virtualenv/bazbia/3.10/bin/python /home/bazbiair/bazbia/manage.py send_daily_telegram_product --exclude-days 30 >> /home/bazbiair/logs/telegram_products.log 2>&1
```

مسیر پروژه، محیط مجازی و پوشه لاگ باید با مسیر واقعی هاست تطبیق داده شوند.
