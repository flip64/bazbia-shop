from django import forms

from products.models import ProductVariant
from suppliers.models import Supplier


class InventoryReceiptForm(forms.Form):
    variant = forms.ModelChoiceField(
        queryset=ProductVariant.objects.select_related(
            "product"
        ).order_by(
            "product__name",
            "id",
        ),
        label="واریانت",
    )

    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.all().order_by(
            "name"
        ),
        required=False,
        label="تأمین‌کننده",
    )

    quantity = forms.IntegerField(
        min_value=1,
        label="تعداد ورود",
    )

    unit_cost = forms.DecimalField(
        min_value=1,
        max_digits=14,
        decimal_places=0,
        label="قیمت خرید هر واحد",
    )

    note = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
            }
        ),
        label="یادداشت",
    )
