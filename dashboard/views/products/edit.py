# -*- coding: utf-8 -*-

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from dashboard.forms import ProductEditForm
from products.models import Product,ProductImage


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





@login_required
def product_variants_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)

    messages.info(
        request,
        "بخش مدیریت ,وایانتها در مرحله بعد تکمیل می‌شود.",
    )

    return redirect(
        "dashboard:product_detail",
        pk=product.pk,
    )


@login_required
def product_images_edit(request, pk):

    product = get_object_or_404(
        Product.objects.prefetch_related("images"),
        pk=pk,
    )

    if request.method == "POST":
        uploaded_image = request.FILES.get("image")

        if not uploaded_image:
            messages.error(
                request,
                "لطفاً یک فایل تصویر انتخاب کنید.",
            )

        else:
            allowed_content_types = {
                "image/jpeg",
                "image/png",
                "image/webp",
            }

            if uploaded_image.content_type not in allowed_content_types:
                messages.error(
                    request,
                    "فقط تصاویر JPG، PNG و WEBP مجاز هستند.",
                )

            elif uploaded_image.size > 5 * 1024 * 1024:
                messages.error(
                    request,
                    "حجم تصویر نباید بیشتر از ۵ مگابایت باشد.",
                )

            else:
                has_main_image = product.images.filter(
                    is_main=True,
                ).exists()

                ProductImage.objects.create(
                    product=product,
                    image=uploaded_image,
                    alt_text=product.name,
                    is_main=not has_main_image,
                )

                messages.success(
                    request,
                    "تصویر با موفقیت آپلود شد.",
                )

                return redirect(
                    "dashboard:product_images_edit",
                    pk=product.pk,
                )

    context = {
        "page_title": f"مدیریت تصاویر {product.name}",
        "product": product,
        "product_images": product.images.all(),
    }

    return render(
        request,
        "dashboard/pages/product_edit/product_images_edit.html",
        context,
    )

def product_image_delete(request, image_id):
    image = get_object_or_404(
        ProductImage,
        pk=image_id,
    )

    product_pk = image.product_id

    if request.method == "POST":
        image.delete()

        messages.success(
            request,
            "تصویر با موفقیت حذف شد.",
        )

    return redirect(
        "dashboard:product_images_edit",
        pk=product_pk,
    )

