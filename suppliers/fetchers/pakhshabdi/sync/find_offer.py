from suppliers.models import SupplierOffer


def find_offer_by_url(supplier, url):
    """
    جستجوی پیشنهاد تأمین‌کننده بر اساس تأمین‌کننده و لینک محصول.

    Parameters
    ----------
    supplier : Supplier
    url : str

    Returns
    -------
    SupplierOffer | None
    """
    return (
        SupplierOffer.objects
        .filter(
            supplier=supplier,
            supplier_url=url,
        )
        .select_related("variant", "supplier")
        .first()
    )