import itertools

def max_items_in_box(box_dims, item_dims):
    """
    محاسبه بیشترین تعداد آیتمی که در یک جعبه جا می‌شود.
    """
    L_box, W_box, H_box = box_dims
    l_item, w_item, h_item = item_dims
    rotations = set(itertools.permutations([l_item, w_item, h_item]))
    max_count = 0
    for rot in rotations:
        l, w, h = rot
        nx = L_box // l
        ny = W_box // w
        nz = H_box // h
        count = nx * ny * nz
        if count > max_count:
            max_count = count
    return max_count


class TrimLargeBoxesFilter:
    def filter(self, boxes, items):
        if not items:
            return boxes

        # بزرگ‌ترین ابعاد هر آیتم
        max_length = max(i["length"] for i in items)
        max_width  = max(i["width"]  for i in items)
        max_height = max(i["height"] for i in items)
        count_items = len(items)

        # مکعب فرضی
        cube = (max_length, max_width, max_height)
        # مرتب‌سازی جعبه‌ها بر اساس حجم (کوچک به بزرگ)
        def volume(b):
            return b["length"] * b["width"] * b["height"]

        boxes_sorted = sorted(boxes, key=volume)

        for i, box in enumerate(boxes_sorted):
            box_dims = (box["length"], box["width"], box["height"])
            max_fit = max_items_in_box(box_dims, cube)
            if max_fit >= count_items:
                # همه جعبه‌های کوچکتر یا خود جعبه در خروجی
                return boxes_sorted[:i+1]

        # اگر هیچ جعبه‌ای جا نشد → تمام جعبه‌ها را بده
        return boxes_sorted
