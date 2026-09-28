from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from core.logging_config import get_logger
from products.models import Category

from basalam_integration.models import BasalamCategoryMapping
from dashboard.forms import BasalamCategoryManagementForm


logger = get_logger(__name__)


def _category_queryset():
    return (
        Category.objects.select_related(
            "parent",
            "basalam_mapping__basalam_category",
        )
        .annotate(
            product_count=Count("products", distinct=True),
            child_count=Count("subcategories", distinct=True),
        )
        .order_by("name")
    )


@staff_member_required
def basalam_category_management(request):
    edit_category = None
    bound_form = None

    if request.method == "POST":
        action = request.POST.get("action", "").strip()
        category_id = request.POST.get("category_id")

        if action == "save":
            edit_category = (
                get_object_or_404(Category, pk=category_id)
                if category_id
                else Category()
            )
            bound_form = BasalamCategoryManagementForm(
                request.POST,
                request.FILES,
                instance=edit_category,
            )
            if bound_form.is_valid():
                with transaction.atomic():
                    category = bound_form.save()
                    mapping = bound_form.save_mapping(category)
                logger.info(
                    "دسته بازبیا و نگاشت باسلام ذخیره شد | "
                    "category_id=%s | basalam_category_id=%s",
                    category.pk,
                    mapping.basalam_category.basalam_category_id
                    if mapping
                    else "-",
                )
                messages.success(request, "دسته و نگاشت آن ذخیره شد.")
                return redirect("dashboard:basalam_categories")
            messages.error(request, "اطلاعات فرم را بررسی کنید.")

        elif action == "unmap":
            category = get_object_or_404(Category, pk=category_id)
            deleted, _ = BasalamCategoryMapping.objects.filter(
                bazbia_category=category
            ).delete()
            if deleted:
                logger.info(
                    "نگاشت دسته باسلام حذف شد | category_id=%s",
                    category.pk,
                )
                messages.success(request, "نگاشت دسته حذف شد.")
            else:
                messages.info(request, "این دسته نگاشتی نداشت.")
            return redirect("dashboard:basalam_categories")

        elif action == "delete":
            category = get_object_or_404(
                _category_queryset(),
                pk=category_id,
            )
            if category.product_count or category.child_count:
                messages.error(
                    request,
                    "این دسته محصول یا زیردسته دارد و قابل حذف نیست. "
                    "ابتدا وابستگی‌ها را منتقل کنید.",
                )
            else:
                category_name = category.name
                category_pk = category.pk
                category.delete()
                logger.info(
                    "دسته خالی بازبیا حذف شد | "
                    "category_id=%s | category=%s",
                    category_pk,
                    category_name,
                )
                messages.success(request, "دسته خالی حذف شد.")
            return redirect("dashboard:basalam_categories")

        else:
            messages.error(request, "عملیات انتخاب‌شده معتبر نیست.")
            return redirect("dashboard:basalam_categories")

    elif request.GET.get("edit", "").isdigit():
        edit_category = get_object_or_404(
            Category,
            pk=int(request.GET["edit"]),
        )

    search = request.GET.get("search", "").strip()
    mapping_status = request.GET.get("mapping", "").strip()
    queryset = _category_queryset()

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search)
            | Q(slug__icontains=search)
            | Q(basalam_mapping__basalam_category__title__icontains=search)
        )
    if mapping_status == "mapped":
        queryset = queryset.filter(
            basalam_mapping__isnull=False,
            basalam_mapping__is_active=True,
        )
    elif mapping_status == "unmapped":
        queryset = queryset.filter(
            Q(basalam_mapping__isnull=True)
            | Q(basalam_mapping__is_active=False)
        )
    else:
        mapping_status = ""

    paginator = Paginator(queryset, 30)
    page_obj = paginator.get_page(request.GET.get("page"))
    form = bound_form or BasalamCategoryManagementForm(instance=edit_category)
    total = Category.objects.count()
    mapped = BasalamCategoryMapping.objects.filter(is_active=True).count()

    return render(
        request,
        "dashboard/pages/basalam/category_list.html",
        {
            "page_title": "دسته‌بندی و نگاشت باسلام",
            "categories": page_obj.object_list,
            "page_obj": page_obj,
            "paginator": paginator,
            "is_paginated": page_obj.has_other_pages(),
            "form": form,
            "edit_category": edit_category if edit_category and edit_category.pk else None,
            "search": search,
            "mapping_status": mapping_status,
            "statistics": {
                "all": total,
                "mapped": mapped,
                "unmapped": total - mapped,
            },
            "query_without_page": "&".join(
                f"{key}={value}"
                for key, value in request.GET.items()
                if key not in {"page", "edit"}
            ),
        },
    )
