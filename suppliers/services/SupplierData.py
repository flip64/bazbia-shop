# -*- coding: utf-8 -*-


class SupplierData(object):
    """
    کلاس استاندارد انتقال اطلاعات تأمین‌کننده بین Extractor و SupplierCreator

    تمام استخراج‌کننده‌ها در صورت نیاز به ایجاد یا بروزرسانی
    تأمین‌کننده باید از این کلاس استفاده کنند.
    """

    def __init__(self):

        # ==========================
        # اطلاعات اصلی
        # ==========================
        self.name = None

        # ==========================
        # اطلاعات تماس
        # ==========================
        self.slug = None
        self.website = None
        self.phone = None
        self.email = None
        self.address = None

        # ==========================
        # وضعیت
        # ==========================
        self.is_active = True

        # ==========================
        # اطلاعات داخلی
        # ==========================
        self.note = ""

    def __repr__(self):
        return "<SupplierData name={!r}>".format(self.name)
