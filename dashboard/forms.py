# -*- coding: utf-8 -*-

from decimal import Decimal

from django import forms

from django.forms import inlineformset_factory

from products.models import Product, ProductVariant


class ProductEditForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "slug",
            "category",
            "description",
            "is_active",
        ]


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = [
            "sku",
            "price",
            "discount_price",
            "low_stock_threshold",
            "profit_percent",
            "expiration_date",
            "attributes",
        ]
        widgets = {
            "expiration_date": forms.DateInput(attrs={"type": "date"}),
            "attributes": forms.SelectMultiple(attrs={"size": 4}),
        }
        labels = {
            "sku": "کد کالا (SKU)",
            "price": "قیمت فروش (تومان)",
            "discount_price": "قیمت تخفیفی (تومان)",
            "low_stock_threshold": "آستانه کمبود موجودی",
            "profit_percent": "درصد سود",
            "expiration_date": "تاریخ انقضا",
            "attributes": "ویژگی‌ها",
        }

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get("price")
        discount_price = cleaned_data.get("discount_price")
        profit_percent = cleaned_data.get("profit_percent")

        if price is not None and price < 0:
            self.add_error("price", "قیمت فروش نمی‌تواند منفی باشد.")

        if discount_price is not None:
            if discount_price < 0:
                self.add_error(
                    "discount_price",
                    "قیمت تخفیفی نمی‌تواند منفی باشد.",
                )
            elif price is not None and discount_price >= price:
                self.add_error(
                    "discount_price",
                    "قیمت تخفیفی باید از قیمت فروش کمتر باشد.",
                )

        if profit_percent is not None and not (
            Decimal("0") <= profit_percent <= Decimal("999.99")
        ):
            self.add_error(
                "profit_percent",
                "درصد سود باید بین صفر تا ۹۹۹٫۹۹ باشد.",
            )

        return cleaned_data


ProductVariantFormSet = inlineformset_factory(
    Product,
    ProductVariant,
    form=ProductVariantForm,
    extra=1,
    can_delete=False,
)
