"""Task oriented forms: users never select product/image foreign keys."""
from django import forms
from . import models as m

def validate_sale(form, data):
    if not data.get('sale_mode'):
        form.add_error('sale_mode', 'نحوه فروش را انتخاب کنید.')
    if data.get('price') is None:
        form.add_error('price', 'قیمت فروش را وارد کنید؛ برای پیش‌نویس می‌توانید صفر بگذارید.')
    if data.get('quantity') and data.get('unit_cost') is None:
        form.add_error('unit_cost', 'برای ورود موجودی، بهای خرید هر واحد را وارد کنید.')
    if data.get('sale_mode') == m.SaleMode.UNIQUE and (data.get('quantity') or 0) > 1:
        form.add_error('quantity', 'سکه یا پک اختصاصی فقط یک عدد است؛ برای چند نمونه گزینه مشابه را انتخاب کنید.')


class PackForm(forms.Form):
    name = forms.CharField(label='نام پک', max_length=200)
    issuer = forms.ModelChoiceField(label='کشور (خالی: چند کشور)', queryset=m.CoinIssuer.objects.all(), required=False)
    year = forms.IntegerField(label='سال پک')
    calendar = forms.ChoiceField(label='تقویم', choices=m.Calendar.choices, initial=m.Calendar.GREGORIAN)
    description = forms.CharField(label='توضیحات پک', widget=forms.Textarea, required=False)
    photo = forms.ImageField(label='عکس کامل پک', required=False)
    price = forms.DecimalField(label='قیمت فروش (تومان)', max_digits=12, decimal_places=0, min_value=0, required=False)
    sale_mode = forms.ChoiceField(label='نحوه فروش', choices=m.SaleMode.choices, initial=m.SaleMode.SIMILAR)
    quantity = forms.IntegerField(label='تعداد پک آماده ورودی به انبار', min_value=0, initial=0, required=False)
    unit_cost = forms.DecimalField(label='قیمت خرید هر پک (تومان)', max_digits=14, decimal_places=0, min_value=0, required=False)

    def clean(self):
        d = super().clean()
        validate_sale(self, d)
        return d


class PackItemForm(forms.Form):
    issue = forms.ModelChoiceField(label='سکه داخل پک', queryset=m.CoinIssue.objects.select_related('coin_type__issuer'))
    quantity = forms.IntegerField(label='تعداد در هر پک', min_value=1, max_value=32767, initial=1)
    obverse = forms.ImageField(label='عکس روی این سکه در پک', required=False)
    reverse = forms.ImageField(label='عکس پشت این سکه در پک', required=False)

PackItems = forms.formset_factory(PackItemForm, extra=1, can_delete=True, max_num=100, validate_max=True)
