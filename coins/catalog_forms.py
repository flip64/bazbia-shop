from django import forms
from products.models import ProductVariant
from . import models as m


class CatalogCoinForm(forms.ModelForm):
    obverse = forms.ImageField(label="عکس مرجع روی سکه", required=False)
    reverse = forms.ImageField(label="عکس مرجع پشت سکه", required=False)

    class Meta:
        model = m.CoinType
        exclude = ("slug",)


class VariantConnectionForm(forms.Form):
    issue = forms.ModelChoiceField(label="سال و نوع ضرب", queryset=m.CoinIssue.objects.none())
    variant = forms.ModelChoiceField(label="واریانت محصول", queryset=ProductVariant.objects.none())

    def __init__(self, *args, coin, variant_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["issue"].queryset = coin.issues.all()
        if variant_id and str(variant_id).isdecimal():
            self.fields["variant"].queryset = ProductVariant.objects.filter(pk=variant_id).select_related("product")
