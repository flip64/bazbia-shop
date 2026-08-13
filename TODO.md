# TODO بازبیا

## 🎯 Current Sprint

- [ ] بازنویسی `suppliers/sync/updater.py`
- [ ] اتصال `import_product.py` به `offer_updater`
- [ ] تکمیل سرویس ثبت تاریخچه قیمت
- [ ] تست کامل فرآیند Update قیمت و موجودی

---

## Suppliers

### Sync

- [x] ایجاد `offer_creator`
- [x] ایجاد `offer_updater`
- [ ] بازنویسی `sync/updater.py`
- [ ] اتصال `import_product.py` به `offer_updater`
- [ ] انتقال ثبت تاریخچه قیمت به سرویس مستقل
- [ ] حذف بروزرسانی خودکار `is_available`
- [ ] تست کامل Update قیمت و موجودی

---

### Import

- [ ] عمومی کردن `import_product.py`
- [ ] ساخت Runner برای هر Supplier
- [ ] اصلاح فایل‌های `.sh`

---

### Offer

- [ ] بازبینی `find_offer`
- [ ] بازبینی `create_product`

---

### Inventory

- [ ] ساخت سرویس محاسبه موجودی قابل فروش

---

### Supplier Selector

- [ ] طراحی موتور انتخاب تأمین‌کننده

---

### Tests

- [ ] تست Offer Creator
- [ ] تست Offer Updater
- [ ] تست Sync
- [ ] تست Price History
