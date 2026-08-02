from suppliers.models import Supplier
from suppliers.services.SupplierData import SupplierData


def create_supplier(data: SupplierData) -> Supplier:
    """
    ایجاد تأمین‌کننده

    اگر تأمین‌کننده‌ای با همین نام وجود داشته باشد،
    همان رکورد برگردانده می‌شود.
    """

    supplier, _ = Supplier.objects.get_or_create(
        name=data.name,
        defaults={
            "website": data.website,
            "phone": data.phone,
            "email": data.email,
            "address": data.address,
            "is_active": data.is_active,
            "note": data.note,
        },
    )

    return supplier
