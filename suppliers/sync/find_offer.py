from suppliers.models import SupplierOffer
from suppliers.services.get_supplier import get_supplier


def find_offer(productData):
    """
    جستجوی پیشنهاد تأمین‌کننده بر اساس   محصول.

    Parameters
    ----------
    supplier : productdata.supplier
    url : str

    Returns
    -------
    SupplierOffer | None
    """
    supplier = get_supplier(productData.supplier)
    supplier_url = productData.supplier_url
    return (
        SupplierOffer.objects.filter(supplier=supplier, supplier_url=supplier_url)
        .select_related("variant", "supplier")
        .first()
    )
