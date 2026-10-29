from django import forms
from products.models import ProductVariant
from . import models as m


class CatalogCoinForm(forms.ModelForm):
    mint_year = forms.IntegerField(label="سال ضرب", required=True)

    obverse = forms.ImageField(label="عکس مرجع روی سکه", required=False)
    reverse = forms.ImageField(label="عکس مرجع پشت سکه", required=False)

    class Meta:
        model = m.CoinType
        exclude = ("slug", "year_start", "year_end")


class VariantConnectionForm(forms.Form):
    issue = forms.ModelChoiceField(label="سال و نوع ضرب", queryset=m.CoinIssue.objects.none())
    variant = forms.ModelChoiceField(label="واریانت محصول", queryset=ProductVariant.objects.none())

    def __init__(self, *args, coin, variant_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["issue"].queryset = coin.issues.all()
        issues = list(self.fields["issue"].queryset[:2])
        if len(issues) == 1:
            self.fields["issue"].initial = issues[0].pk
            self.fields["issue"].widget = forms.HiddenInput()
            if self.is_bound and not self.data.get("issue"):
                self.data = self.data.copy()
                self.data["issue"] = issues[0].pk
        if variant_id and str(variant_id).isdecimal():
            self.fields["variant"].queryset = ProductVariant.objects.filter(pk=variant_id).select_related("product")
