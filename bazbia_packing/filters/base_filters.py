# bazbia_packing/filters/base_filters.py

from bazbia_packing.filters.one_item_filter import OneItemFilter
from bazbia_packing.filters.volume_filter import VolumeFilter
from bazbia_packing.filters.dimension_fit_filter import DimensionFitFilter
from bazbia_packing.filters.split_items_filter import SplitItemsFilter  #  


EXCLUDED_BOXES = ["box8", "box9"]


def filter_boxes(boxes, items):
    """
    مدیریت کامل فیلترینگ جعبه‌ها
    """

    if not boxes or not items:
        return []

    # 1) حالت تک‌آیتم
    if len(items) == 1:
        return OneItemFilter().filter(boxes, items)

    # 2) اجرای VolumeFilter
    volume_filtered = VolumeFilter().filter(boxes, items)

    # اگر حجم اجازه نداد → تقسیم‌بندی
    if not volume_filtered:
        return SplitItemsFilter().filter(boxes, items)

    # 3) اگر فقط یک جعبه خروجی داشت
    if len(volume_filtered) == 1:
        box = volume_filtered[0]

        # اگر جعبه جزو استثنایی‌ها نیست همان را برگردان
        if box["name"] not in EXCLUDED_BOXES:
            return [box]

        # اگر box8 یا box9 بود → DimensionFit
        dimension_filtered = DimensionFitFilter().filter([box], items)

        # اگر DimensionFit هم جواب نداد → تقسیم آیتم‌ها
        if not dimension_filtered:
            return SplitItemsFilter().filter(boxes, items)

        return dimension_filtered

    # 4) اگر چند جعبه برگشت ولی DimensionFit لازم نبود → همان را برگردان
    return volume_filtered
