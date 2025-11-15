# bazbia_packing/filters/base_filters.py

from bazbia_packing.filters.one_item_filter import OneItemFilter
from bazbia_packing.filters.volume_filter import VolumeFilter

def filter_boxes(boxes, items):
    """
    مدیریت فیلترها:
    - اگر فقط یک آیتم باشد: OneItemFilter اجرا شود
    - اگر چند آیتم باشد: VolumeFilter اجرا شود
    """

    if not boxes or not items:
        return []

    if len(items) == 1:
        return OneItemFilter().filter(boxes, items)
    else:
        return VolumeFilter().filter(boxes, items)
