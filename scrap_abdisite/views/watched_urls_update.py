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
        # دریافت داده‌های فرم
        price_input = request.POST.get('price')
        discount_price_input = request.POST.get('discount_price')
        profit_percent_input = request.POST.get('profit_percent')

        # بروزرسانی درصد سود
        if profit_percent_input:
            try:
                variant.profit_percent = Decimal(profit_percent_input)
            except:
                messages.error(request, "ورودی درصد سود معتبر نیست.")
                return redirect("scrap_abdisite:product_price_list")

        # بروزرسانی قیمت فروش بر اساس purchase_price و profit_percent
        if variant.purchase_price is not None and variant.profit_percent is not None:
            final_price = variant.purchase_price * (Decimal(1) + variant.profit_percent / Decimal(100))
            variant.price = final_price.quantize(Decimal('100'), rounding=ROUND_HALF_UP)

        # اگر کاربر قیمت را دستی وارد کرده باشد، آن را هم اعمال کن
        if price_input:
            try:
                variant.price = int(price_input)
            except ValueError:
                messages.error(request, "ورودی قیمت معتبر نیست.")
                return redirect("scrap_abdisite:product_price_list")

        # بروزرسانی قیمت تخفیف
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

        variant.save()
        messages.success(request, f"✅ قیمت و درصد سود '{variant.product.name}' بروزرسانی شد.")

    except Exception as e:
        messages.error(request, f"خطا در بروزرسانی: {e}")

    return redirect("scrap_abdisite:product_price_list")
