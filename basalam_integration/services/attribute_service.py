from dataclasses import dataclass
from typing import Any

from basalam_integration.models import (
    BasalamCategory,
    BasalamCategoryAttributeSnapshot,
)

from .client import BasalamClient


@dataclass(frozen=True)
class CategoryAttributeSyncResult:
    category_id: int
    title: str
    attributes_count: int
    saved: bool


def extract_attributes(
    response: Any,
) -> list:
    """
    استخراج فهرست ویژگی‌ها از شکل‌های مختلف پاسخ API.

    پاسخ کامل API همچنان در raw_payload ذخیره می‌شود.
    """

    if isinstance(response, list):
        return response

    if not isinstance(response, dict):
        return []

    attributes = response.get("attributes")

    if isinstance(attributes, list):
        return attributes

    data = response.get("data")

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        attributes = data.get("attributes")

        if isinstance(attributes, list):
            return attributes

        items = data.get("items")

        if isinstance(items, list):
            return items

    result = response.get("result")

    if isinstance(result, list):
        return result

    if isinstance(result, dict):
        attributes = result.get("attributes")

        if isinstance(attributes, list):
            return attributes

    return []


def get_mapped_basalam_categories():
    """
    فقط دسته‌های باسلامی که به دسته‌های بازبیا
    نگاشت فعال دارند.
    """

    return (
        BasalamCategory.objects
        .filter(
            is_active=True,
            bazbia_mappings__is_active=True,
        )
        .distinct()
        .order_by("title")
    )


def sync_category_attributes(
    basalam_category,
    *,
    client: BasalamClient | None = None,
    save: bool = True,
) -> CategoryAttributeSyncResult:
    """
    دریافت ویژگی‌های یک دسته باسلام و ذخیره پاسخ کامل.
    """

    client = client or BasalamClient()

    response = client.get_category_attributes(
        basalam_category.basalam_category_id
    )

    attributes = extract_attributes(
        response
    )

    if save:
        BasalamCategoryAttributeSnapshot.objects.update_or_create(
            basalam_category=basalam_category,
            defaults={
                "raw_payload": response,
                "attributes_count": len(attributes),
                "last_error": "",
            },
        )

    return CategoryAttributeSyncResult(
        category_id=(
            basalam_category.basalam_category_id
        ),
        title=basalam_category.title,
        attributes_count=len(attributes),
        saved=save,
    )
