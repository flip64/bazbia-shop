from suppliers.models import Supplier


def create_supplier(
    name,
    website=None,
    phone=None,
    email=None,
    address=None,
    note="",
):
    """
    ایجاد تأمین‌کننده

    اگر تأمین‌کننده‌ای با همین نام وجود داشته باشد،
    همان رکورد برگردانده می‌شود.
    """

    supplier, created = Supplier.objects.get_or_create(
        name=name,
        defaults={
            "website": website,
            "phone": phone,
            "email": email,
            "address": address,
            "note": note,
        },
    )

    return supplier
