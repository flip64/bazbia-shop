# -*- coding: utf-8 -*-

from decimal import Decimal

from django import forms

from django.forms import inlineformset_factory

from products.models import Category, Product, ProductVariant
from basalam_integration.models import (
    BasalamCategory,
    BasalamCategoryMapping,
)


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


class BasalamCategoryManagementForm(forms.ModelForm):
    slug = forms.SlugField(
        allow_unicode=True,
        label="نامک",
        help_text="برای آدرس و شناسایی دسته استفاده می‌شود.",
    )
    basalam_category = forms.ModelChoiceField(
        queryset=BasalamCategory.objects.none(),
        required=False,
        label="دسته متناظر در باسلام",
        empty_label="بدون نگاشت",
    )
    mapping_active = forms.BooleanField(
        required=False,
        initial=True,
        label="نگاشت فعال باشد",
    )

    class Meta:
        model = Category
        fields = ["name", "slug", "parent", "image"]
        labels = {
            "name": "نام دسته بازبیا",
            "parent": "دسته والد",
            "image": "تصویر دسته",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            css_class = (
                "form-check-input"
                if isinstance(field.widget, forms.CheckboxInput)
                else "form-control"
            )
            if isinstance(field.widget, forms.Select):
                css_class = "form-select"
            field.widget.attrs["class"] = css_class
        self.fields["parent"].queryset = Category.objects.order_by("name")
        self.fields["parent"].required = False
        self.fields["basalam_category"].queryset = (
            BasalamCategory.objects.filter(is_active=True).order_by("title")
        )

        if self.instance and self.instance.pk:
            excluded_ids = {self.instance.pk}
            pending_ids = [self.instance.pk]
            while pending_ids:
                child_ids = list(
                    Category.objects.filter(parent_id__in=pending_ids)
                    .exclude(pk__in=excluded_ids)
                    .values_list("pk", flat=True)
                )
                excluded_ids.update(child_ids)
                pending_ids = child_ids
            self.fields["parent"].queryset = (
                self.fields["parent"].queryset.exclude(pk__in=excluded_ids)
            )
            try:
                mapping = self.instance.basalam_mapping
            except BasalamCategoryMapping.DoesNotExist:
                mapping = None
            if mapping:
                self.fields["basalam_category"].initial = (
                    mapping.basalam_category_id
                )
                self.fields["mapping_active"].initial = mapping.is_active

    def save_mapping(self, category):
        basalam_category = self.cleaned_data.get("basalam_category")
        if basalam_category is None:
            BasalamCategoryMapping.objects.filter(
                bazbia_category=category
            ).delete()
            return None

        mapping, _ = BasalamCategoryMapping.objects.update_or_create(
            bazbia_category=category,
            defaults={
                "basalam_category": basalam_category,
                "is_active": self.cleaned_data.get("mapping_active", False),
            },
        )
        return mapping
