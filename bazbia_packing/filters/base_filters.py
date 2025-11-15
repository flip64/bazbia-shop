# bazbia_packing/filters/base_filters.py

from bazbia_packing.filters.one_item_filter import OneItemFilter
from bazbia_packing.filters.volume_filter import volume_filter  # فرض می‌کنیم این هم تابع است

# نمونه‌ای از مدیریت فیلترها
def filter_boxes(boxes, items):
    """
    مدیریت فیلترها:
    - اگر یک آیتم باشد: OneItemFilter اجرا شود
    - اگر چند آیتم باشد: VolumeFilter اجرا شود
    """

    if not boxes or not items:
        return []

    if len(items) == 1:
        # اجرای فیلتر کلاس OneItemFilter
        return OneItemFilter().filter(boxes, items)
    else:
        # اجرای فیلتر حجم برای چند آیتم
        return volume_filter(boxes, items)
