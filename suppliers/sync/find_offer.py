from suppliers.models import SupplierOffer


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
    supplier = productData.supplier
    supplier_url = productData.supplier_url
    return (
        SupplierOffer.objects
        .filter(
            supplier=supplier,
            supplier_url= supplier_url
        )
        .select_related("variant", "supplier")
        .first()
    )