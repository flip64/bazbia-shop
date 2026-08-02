from suppliers.services.SupplierData import SupplierData
from suppliers.services.get_supplier import get_supplier
from suppliers.services.create_supplier import create_supplier


def get_or_create_supplier():
    supplier = get_supplier("پخش عبدی")

    if supplier is None:
        data = SupplierData()
        data.name = "پخش عبدی"
        data.website = "https://pakhshabdi.com"
        data.phone = ""
        data.email = ""
        data.address = ""
        data.note = "تأمین‌کننده اصلی بازبیا"

        supplier = create_supplier(data)

    return supplier
