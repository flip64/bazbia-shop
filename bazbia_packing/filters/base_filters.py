# bazbia_packing/filters/base_filters.py

from bazbia_packing.filters.one_item_filter import one_item_filter
from bazbia_packing.filters.volume_filter import volume_filter
# سایر فیلترها هم می‌توانند اضافه شوند

def filter_boxes(boxes, items):
    """
    فقط مدیریت فیلترها:
    - اگر یک آیتم باشد: OneItemFilter اجرا شود
    - اگر چند آیتم باشد: VolumeFilter اجرا شود
    """

    if not boxes or not items:
        return []

    if len(items) == 1:
        # فراخوانی فیلتر مخصوص یک آیتم
        return one_item_filter(boxes, items[0])
    else:
        # فراخوانی فیلتر مخصوص چند آیتم
        return volume_filter(boxes, items)
