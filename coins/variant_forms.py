from decimal import Decimal
from django import forms
from products.models import ProductVariant, ProductVariantImage
from .models import CoinImageDetail


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


class CoinVariantImageForm(forms.ModelForm):
    view_type = forms.ChoiceField(
        label="نمای تصویر", choices=CoinImageDetail.View.choices
    )
    caption = forms.CharField(label="شرح تصویر", required=False, max_length=255)

    class Meta:
        model = ProductVariantImage
        fields = ("variant", "image", "source_url", "alt_text", "is_main")
        labels = {
            "variant": "واریانت",
            "image": "فایل عکس",
            "source_url": "نشانی عکس (اختیاری)",
            "alt_text": "متن جایگزین",
            "is_main": "تصویر اصلی واریانت",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        detail = (
            getattr(self.instance, "coin_detail", None) if self.instance.pk else None
        )
        if detail:
            self.fields["view_type"].initial = detail.view_type
            self.fields["caption"].initial = detail.caption

    def clean(self):
        values = super().clean()
        if not values.get("image") and not values.get("source_url"):
            raise forms.ValidationError("فایل عکس یا نشانی آن را وارد کنید.")
        return values

    def save(self, commit=True):
        from .models import CoinImageDetail

        image = super().save(commit=commit)
        if commit:
            detail = getattr(image, "coin_detail", None) or CoinImageDetail(image=image)
            detail.view_type = self.cleaned_data["view_type"]
            detail.caption = self.cleaned_data["caption"]
            detail.save()
        return image
