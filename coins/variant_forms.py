from decimal import Decimal
from django import forms
from products.models import ProductVariant


class QuickVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ("product", "sku", "price", "discount_price")

    def clean(self):
        data = super().clean()
        price, discount = data.get("price"), data.get("discount_price")
        if price is not None and price < Decimal("0"):
            self.add_error("price", "قیمت نمی‌تواند منفی باشد.")
        if discount is not None and (
            discount < 0 or (price is not None and discount >= price)
        ):
            self.add_error(
                "discount_price", "قیمت تخفیفی باید غیرمنفی و کمتر از قیمت اصلی باشد."
            )
        return data
