from functions import lru_cache 
from suppliers.services.SupplierData import SupplierData
from suppliers.services.get_supplier import get_supplier
from suppliers.services.create_supplier import create_supplier

@lru_cache
def get_supplier_abdi():
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
