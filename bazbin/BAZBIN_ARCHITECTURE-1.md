# معماری اپ Bazbin

این فایل معماری اولیه اپ `bazbin` را مشخص می‌کند. هدف این اپ، مدیریت DNA دیجیتال بازبین، ساخت ویژگی‌ها، تولید پرامپت، تولید تصویر و نگهداری اطلاعات تصاویر تولیدشده است.

## هدف اصلی

اپ `bazbin` باید بتواند:

- برای هر بازبین یک DNA یکتا بسازد.
- ویژگی‌های ظاهری را از روی DNA تولید کند.
- میزان کمیابی هر ویژگی را محاسبه کند.
- پرامپت مناسب برای موتور تولید تصویر بسازد.
- تصویر تولیدشده را در Storage ذخیره کند.
- مسیر تصویر و اطلاعات تولید را در دیتابیس ثبت کند.
- امکان بازسازی دوباره یک بازبین از روی DNA و Seed را فراهم کند.

## ساختار پیشنهادی

```text
bazbin/
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── urls.py
├── views.py
├── serializers.py
├── selectors.py
├── constants.py
├── exceptions.py
├── migrations/
├── services/
│   ├── __init__.py
│   ├── dna_generator.py
│   ├── trait_generator.py
│   ├── rarity_calculator.py
│   ├── prompt_builder.py
│   ├── image_generator.py
│   ├── image_storage.py
│   └── bazbin_creator.py
├── management/
│   └── commands/
│       ├── __init__.py
│       └── generate_bazbin.py
└── tests/
    ├── __init__.py
    ├── test_dna_generator.py
    ├── test_trait_generator.py
    ├── test_prompt_builder.py
    └── test_bazbin_creator.py
```

## مسئولیت فایل‌ها

### `models.py`

مدل‌های دیتابیس این اپ در این فایل قرار می‌گیرند.

مدل‌های اولیه پیشنهادی:

- `Bazbin`
- `BazbinTrait`
- `BazbinImage`
- `BazbinGeneration`

### `constants.py`

مقادیر ثابت مانند رنگ‌ها، فرم چشم، فرم بال، نوع بدن، سطح کمیابی و نسخه DNA در این فایل نگهداری می‌شوند.

### `selectors.py`

توابع فقط خواندنی دیتابیس در این فایل قرار می‌گیرند.

نمونه:

```python
def get_bazbin_by_dna(dna: str):
    ...
```

### `services/dna_generator.py`

مسئول تولید DNA یکتا و پایدار است.

ورودی احتمالی:

- شناسه سفارش
- شناسه کاربر
- شماره بازبین
- مقدار تصادفی امن

خروجی:

```text
BZ1-A7F2-C19D-8E42-91AB
```

### `services/trait_generator.py`

DNA را به ویژگی‌های قابل استفاده تبدیل می‌کند.

نمونه ویژگی‌ها:

- رنگ بدن
- رنگ بال
- رنگ چشم
- فرم چشم
- فرم منقار
- فرم دم
- فرم تاج
- طرح بدن
- اندازه بدن
- ویژگی ویژه

### `services/rarity_calculator.py`

بر اساس احتمال هر ویژگی، میزان کمیابی بازبین را محاسبه می‌کند.

سطوح پیشنهادی:

- common
- uncommon
- rare
- epic
- legendary

### `services/prompt_builder.py`

ویژگی‌های بازبین را به پرامپت استاندارد تولید تصویر تبدیل می‌کند.

این سرویس نباید مستقیماً تصویر بسازد.

### `services/image_generator.py`

رابط بین پروژه و موتور تولید تصویر است.

در آینده می‌تواند به یکی از این موتورها متصل شود:

- FLUX
- Stable Diffusion
- API خارجی
- مدل محلی

این فایل باید وابستگی به ارائه‌دهنده تصویر را از منطق اصلی اپ جدا نگه دارد.

### `services/image_storage.py`

مسئول ذخیره فایل تصویر در Storage است.

در محیط توسعه:

```text
media/bazbins/
```

در محیط اصلی می‌تواند از Object Storage یا CDN استفاده کند.

### `services/bazbin_creator.py`

سرویس هماهنگ‌کننده اصلی است.

ترتیب عملیات:

1. تولید DNA
2. تولید ویژگی‌ها
3. محاسبه کمیابی
4. ساخت پرامپت
5. ساخت رکورد دیتابیس
6. ارسال درخواست تولید تصویر
7. ذخیره تصویر
8. ثبت اطلاعات نهایی تولید

## مدل داده پیشنهادی

### مدل `Bazbin`

اطلاعات اصلی هر موجود دیجیتال را نگهداری می‌کند.

فیلدهای پیشنهادی:

```text
id
owner
dna
dna_version
name
rarity
traits
status
created_at
updated_at
```

فیلد `traits` می‌تواند در نسخه اول از نوع `JSONField` باشد.

### مدل `BazbinImage`

اطلاعات تصویر بازبین را نگهداری می‌کند.

فیلدهای پیشنهادی:

```text
bazbin
image
width
height
format
file_size
is_primary
created_at
```

خود فایل تصویر داخل دیتابیس ذخیره نمی‌شود. فقط مسیر فایل در دیتابیس ثبت می‌شود.

### مدل `BazbinGeneration`

اطلاعات فنی هر بار تولید تصویر را نگهداری می‌کند.

فیلدهای پیشنهادی:

```text
bazbin
prompt
negative_prompt
provider
model_name
seed
status
error_message
started_at
finished_at
```

این مدل برای بررسی خطاها، تولید مجدد و مقایسه مدل‌ها مفید است.

## وضعیت‌های پیشنهادی تولید

```text
pending
processing
completed
failed
```

## قانون مهم بازسازی

برای اینکه یک بازبین در آینده دوباره با همان ظاهر ساخته شود، این موارد باید ثبت شوند:

- DNA
- نسخه الگوریتم DNA
- ویژگی‌های نهایی
- Prompt
- Seed
- نام مدل تصویر
- نسخه مدل یا تنظیمات مهم تولید

## جریان ساخت بازبین

```text
Order Paid
    ↓
Bazbin Creation Service
    ↓
DNA Generator
    ↓
Trait Generator
    ↓
Rarity Calculator
    ↓
Prompt Builder
    ↓
Image Generator
    ↓
Image Storage
    ↓
Database
```

## نسخه اول پروژه

در نسخه اول بهتر است فقط این بخش‌ها پیاده‌سازی شوند:

1. مدل `Bazbin`
2. مدل `BazbinImage`
3. مدل `BazbinGeneration`
4. تولید DNA
5. تولید ویژگی‌ها
6. ساخت پرامپت
7. دستور مدیریتی برای ساخت آزمایشی بازبین

تولید واقعی تصویر می‌تواند در مرحله بعد اضافه شود.

## دستور آزمایشی آینده

```bash
python manage.py generate_bazbin
```

یا:

```bash
python manage.py generate_bazbin --count 10
```

## اصول معماری

- منطق اصلی داخل `views.py` نوشته نشود.
- تولید DNA از تولید تصویر مستقل باشد.
- موتور تصویر قابل تعویض باشد.
- ویژگی‌های بازبین از روی DNA قابل بازسازی باشند.
- تصاویر در Storage ذخیره شوند، نه به‌صورت Binary داخل دیتابیس.
- هر تغییر مهم الگوریتم با نسخه مشخص ثبت شود.
- عملیات تولید تصویر باید قابل ثبت، تکرار و خطایابی باشد.
