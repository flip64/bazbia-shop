# -*- coding: utf-8 -*-

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from dashboard.forms import ProductEditForm
from products.models import Product


@login_required
def product_info_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        form = ProductEditForm(
            request.POST,
            instance=product,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "اطلاعات اصلی محصول با موفقیت ویرایش شد.",
            )

            return redirect(
                "dashboard:product_detail",
                pk=product.pk,
            )

    else:
        form = ProductEditForm(instance=product)

    context = {
        "page_title": f"ویرایش اطلاعات {product.name}",
        "product": product,
        "form": form,
    }

    return render(
        request,
        "dashboard/pages/product_edit/product_info_edit.html",
        context,
    )



@login_required
def product_images_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)

    messages.info(
        request,
        "بخش مدیریت تصاویر در مرحله بعد تکمیل می‌شود.",
    )

    return redirect(
        "dashboard:product_detail",
        pk=product.pk,
    )


@login_required
def product_specifications_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)

    messages.info(
        request,
        "بخش ویرایش مشخصات در مرحله بعد تکمیل می‌شود.",
    )

    return redirect(
        "dashboard:product_detail",
        pk=product.pk,
    )


@login_required
def product_tags_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)

    messages.info(
        request,
        "بخش مدیریت تگ‌ها در مرحله بعد تکمیل می‌شود.",
    )

    return redirect(
        "dashboard:product_detail",
        pk=product.pk,
    )
