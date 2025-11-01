# -*- coding: utf-8 -*-

from decimal import Decimal, ROUND_HALF_UP
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from scrap_abdisite.models import WatchedURL


def watched_urls_update(request, watched_id):
    """ویوی بروزرسانی درصد سود، قیمت و قیمت تخفیف واریانت‌ها"""
    watched = get_object_or_404(WatchedURL, id=watched_id)
    variant = watched.variant

    if not variant:
        messages.error(request, "این لینک واریانت ندارد.")
        return redirect("scrap_abdisite:product_price_list")

    try:
        price_input = request.POST.get("price")
        discount_price_input = request.POST.get("discount_price")
        profit_percent_input = request.POST.get("profit_percent")

        # بروزرسانی درصد سود
        if profit_percent_input:
            try:
                profit_percent = Decimal(profit_percent_input)
                variant.profit_percent = profit_percent
            except Exception:
                messages.error(request, "ورودی درصد سود معتبر نیست.")
                return redirect("scrap_abdisite:product_price_list")

            # اگر قیمت خرید موجود است، قیمت فروش را مجدد محاسبه کن
            if variant.purchase_price is not None:
                final_price = variant.purchase_price * (Decimal(1) + profit_percent / Decimal(100))
                variant.price = final_price.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        # اگر قیمت دستی وارد شده، جایگزین کن (در اولویت بالاتر از درصد سود)
        if price_input:
            try:
                variant.price = int(price_input)
            except ValueError:
                messages.error(request, "ورودی قیمت معتبر نیست.")
                return redirect("scrap_abdisite:product_price_list")

        # بروزرسانی قیمت تخفیف
        if discount_price_input:
            try:
                discount_price = int(discount_price_input)
                if discount_price > variant.price:
                    messages.error(request, "قیمت تخفیف نمی‌تواند بیشتر از قیمت اصلی باشد.")
                    return redirect("scrap_abdisite:product_price_list")
                variant.discount_price = discount_price
            except ValueError:
                messages.error(request, "ورودی قیمت تخفیف معتبر نیست.")
                return redirect("scrap_abdisite:product_price_list")
        else:
            variant.discount_price = None

        # ذخیره تغییرات
        variant.save()

        messages.success(
            request,
            f"قیمت محصول «{variant.product.name}» با درصد سود {variant.profit_percent}% بروزرسانی شد. "
            f"(قیمت جدید: {variant.price:,} تومان)"
        )

    except Exception as e:
        messages.error(request, f"خطا در بروزرسانی: {e}")

    return redirect("scrap_abdisite:product_price_list")
