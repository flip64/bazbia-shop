import hashlib
import mimetypes
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction

from basalam_integration.models import (
    BasalamImageMapping,
)

from .client import BasalamClient


@dataclass(frozen=True)
class BasalamUploadedImage:
    product_image_id: int
    basalam_file_id: str
    reused: bool


def get_product_images(product):
    """
    دریافت تصاویر محلی محصول.

    تصویر اصلی در ابتدای فهرست قرار می‌گیرد.
    تصاویری که فقط source_url دارند در این مرحله
    ارسال نمی‌شوند.
    """

    return list(
        product.images
        .exclude(image="")
        .filter(image__isnull=False)
        .order_by(
            "-is_main",
            "id",
        )
    )


def calculate_image_hash(field_file) -> str:
    """
    محاسبه SHA-256 محتوای تصویر.

    با این مقدار متوجه می‌شویم که فایل تصویر
    تغییر کرده است یا خیر.
    """

    digest = hashlib.sha256()

    field_file.open("rb")

    try:
        for chunk in field_file.chunks():
            digest.update(chunk)
    finally:
        field_file.close()

    return digest.hexdigest()


def get_content_type(filename: str) -> str:
    """
    تشخیص نوع فایل از روی نام آن.
    """

    content_type, _ = mimetypes.guess_type(
        filename
    )

    return content_type or "application/octet-stream"


@transaction.atomic
def upload_product_image(
    product_image,
    *,
    client: BasalamClient | None = None,
    force: bool = False,
) -> BasalamUploadedImage:
    """
    آپلود یک تصویر محصول در باسلام.

    اگر محتوای تصویر تغییر نکرده باشد،
    شناسه قبلی دوباره استفاده می‌شود.
    """

    if not product_image.image:
        raise ValidationError(
            "این رکورد فایل تصویر محلی ندارد."
        )

    try:
        file_exists = (
            product_image.image.storage.exists(
                product_image.image.name
            )
        )

        if not file_exists:
            raise ValidationError(
                "فایل تصویر در فضای ذخیره‌سازی پیدا نشد."
            )
    except NotImplementedError:
        # بعضی storageهای ابری متد exists ندارند.
        pass

    content_hash = calculate_image_hash(
        product_image.image
    )

    mapping = (
        BasalamImageMapping.objects
        .filter(
            product_image=product_image,
        )
        .first()
    )

    if (
        mapping
        and mapping.content_hash == content_hash
        and not force
    ):
        return BasalamUploadedImage(
            product_image_id=product_image.pk,
            basalam_file_id=mapping.basalam_file_id,
            reused=True,
        )

    client = client or BasalamClient()

    filename = (
        product_image.image.name
        .rsplit("/", 1)[-1]
    )

    content_type = get_content_type(
        filename
    )

    product_image.image.open("rb")

    try:
        response = client.upload_file(
            file_object=product_image.image.file,
            filename=filename,
            content_type=content_type,
        )
    finally:
        product_image.image.close()

    basalam_file_id = response.get("id")

    if basalam_file_id in (None, ""):
        raise ValidationError(
            "پاسخ آپلود باسلام فاقد شناسه فایل است."
        )

    basalam_file_id = str(
        basalam_file_id
    )

    BasalamImageMapping.objects.update_or_create(
        product_image=product_image,
        defaults={
            "basalam_file_id": basalam_file_id,
            "content_hash": content_hash,
            "last_error": "",
        },
    )

    return BasalamUploadedImage(
        product_image_id=product_image.pk,
        basalam_file_id=basalam_file_id,
        reused=False,
    )


def upload_product_images(
    product,
    *,
    force: bool = False,
):
    """
    آپلود تمام تصاویر محلی یک محصول.

    ترتیب خروجی:
    تصویر اصلی، سپس تصاویر آلبوم.
    """

    images = get_product_images(
        product
    )

    if not images:
        raise ValidationError(
            "محصول هیچ فایل تصویر محلی ندارد."
        )

    client = BasalamClient()

    results = []

    for product_image in images:
        result = upload_product_image(
            product_image,
            client=client,
            force=force,
        )

        results.append(result)

    return results
