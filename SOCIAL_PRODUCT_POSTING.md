# انتشار محصول در بله و تلگرام

## متغیرهای محیطی

```env
BALE_BOT_TOKEN=...
BALE_CHANNEL_ID=@bazbia
BALE_WEBHOOK_SECRET=change_this_to_a_long_random_secret
BALE_ADMIN_USER_IDS=123456789
BALE_RANDOM_EXCLUDE_DAYS=30
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHANNEL_ID=@your_telegram_channel
```

ربات هر شبکه باید مدیر کانال خودش باشد و اجازه ارسال پیام داشته باشد.

`BALE_ADMIN_USER_IDS` شناسه عددی مدیرانی است که اجازه اجرای دستور از داخل
ربات بله را دارند. برای چند مدیر، شناسه‌ها را با ویرگول جدا کنید. ربات هیچ
management command دلخواهی اجرا نمی‌کند و فقط دو دستور ارسال محصول را می‌شناسد.

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

## فعال‌سازی کنترل از داخل ربات بله

بعد از قراردادن متغیرهای بالا و اجرای مجدد برنامه، وب‌هوک را یک بار تنظیم کنید:

```bash
python manage.py set_bale_webhook
```

سپس در گفت‌وگوی خصوصی با ربات بله این دستورها در دسترس‌اند:

```text
/id                 نمایش شناسه کاربری برای تنظیم BALE_ADMIN_USER_IDS
/start              نمایش راهنما و دکمه ارسال تصادفی
/random             اجرای send_random_bale_product
/product 2163       اجرای send_bale_product --product-id 2163
```

دکمه «ارسال محصول تصادفی» نیز همان management command مربوط به ارسال تصادفی
را اجرا می‌کند. محدودیت ۳۰ روزه فقط برای انتخاب تکراری محصول است و با متغیر
`BALE_RANDOM_EXCLUDE_DAYS` قابل تغییر است.

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
