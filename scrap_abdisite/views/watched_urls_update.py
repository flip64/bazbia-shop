from decimal import Decimal, ROUND_HALF_UP
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from scrap_abdisite.models import WatchedURL

def watched_urls_update(request, watched_id):
    watched = get_object_or_404(WatchedURL, id=watched_id)
    variant = watched.variant

    if not variant:
        messages.error(request, "این لینک واریانت ندارد.")
        return redirect("scrap_abdisite:product_price_list")

    try:
        # 🟢 دریافت داده‌های فرم
        price_input = request.POST.get('price')
        discount_price_input = request.POST.get('discount_price')
        profit_percent_input = request.POST.get('profit_percent')

        # 🟢 اگر درصد سود وارد شده، ذخیره شود
        if profit_percent_input:
            try:
                variant.profit_percent = Decimal(profit_percent_input)
            except Exception:
                messages.error(request, "ورودی درصد سود معتبر نیست.")
                return redirect("scrap_abdisite:product_price_list")

        # 🟢 محاسبه قیمت فروش بر اساس قیمت خرید + درصد سود
        if variant.purchase_price is not None and variant.profit_percent is not None:
            final_price = variant.purchase_price * (Decimal(1) + variant.profit_percent / Decimal(100))
            # گرد کردن به نزدیک‌ترین عدد صحیح (مثلاً 12499 ← 12500)
            variant.price = final_price.quantize(Decimal('1'), rounding=ROUND_HALF_UP)

        # 🟢 اگر قیمت دستی وارد شده، جایگزین شود
        if price_input:
            try:
                variant.price = int(price_input)
            except ValueError:
                messages.error(request, "ورودی قیمت معتبر نیست.")
                return redirect("scrap_abdisite:product_price_list")

        # 🟢 بروزرسانی قیمت تخفیف
        if discount_price_input:
            try:
                dp = int(discount_price_input)
                if dp > variant.price:
                    messages.error(request, "قیمت تخفیف نمی‌تواند بیشتر از قیمت اصلی باشد.")
                    return redirect("scrap_abdisite:product_price_list")
                variant.discount_price = dp
            except ValueError:
                messages.error(request, "ورودی قیمت تخفیف معتبر نیست.")
                return redirect("scrap_abdisite:product_price_list")
        else:
            variant.discount_price = None

        # 🟢 ذخیره نهایی تغییرات
        variant.save()

        messages.success(
            request,
            f"✅ قیمت و درصد سود محصول «{variant.product.name}» بروزرسانی شد. "
            f"(قیمت جدید: {variant.price:,} تومان)"
        )

    except Exception as e:
        messages.error(request, f"⚠️ خطا در بروزرسانی: {e}")

    return redirect("scrap_abdisite:product_price_list")
