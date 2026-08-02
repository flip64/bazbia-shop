# -*- coding: utf-8 -*-


class ProductData(object):
    """
    کلاس استاندارد انتقال اطلاعات محصول بین Extractor و ProductCreator

    تمام استخراج‌کننده‌های تأمین‌کننده باید در نهایت یک نمونه از این
    کلاس را برگردانند.
    """

    def __init__(self):

        # ==========================
        # اطلاعات اصلی محصول
        # ==========================
        self.name = None
        self.slug = None
        self.description = ""
        self.category = None

        # ==========================
        # قیمت و موجودی
        # ==========================
        self.price = 0
        self.quantity = 0

        # ==========================
        # رسانه
        # ==========================
        self.images = []
        self.videos = []

        # ==========================
        # مشخصات
        # ==========================
        self.specifications = []

        # ==========================
        # ویژگی ها (رنگ، سایز و ...)
        # ==========================
        self.attributes = []

        # ==========================
        # تگ ها
        # ==========================
        self.tags = []

        # ==========================
        # اطلاعات تأمین کننده
        # ==========================
        self.supplier = None
        self.supplier_url = None
        self.supplier_product_code = None


        # ==========================
        # وضعیت محصول  
        # ==========================
        self.is_active = True



        # ==========================
        # اطلاعات تکمیلی
        # ==========================
        self.brand = None
        self.barcode = None
        self.weight = None

    def __repr__(self):
        return (
            "<ProductData name={!r} price={} quantity={}>"
            .format(self.name, self.price, self.quantity)
        )
