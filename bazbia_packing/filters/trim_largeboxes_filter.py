import itertools

class TrimLargeBoxesFilter:
    def max_items_in_box(self, box_dims, item_dims):
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
            max_count = max(max_count, count)

        return max_count

    def filter(self, boxes, items):
        if not items:
            return boxes

        # -----------------------------------------------------
        # 🔹 ابتدا چک کنیم آیا همه آیتم‌ها هم‌اندازه هستند؟
        # -----------------------------------------------------
        first = (items[0]["length"], items[0]["width"], items[0]["height"])
        all_same_size = all(
            (i["length"], i["width"], i["height"]) == first
            for i in items
        )

        # -----------------------------------------------------
        # 🟦 حالت ویژه: تمام آیتم‌ها هم‌اندازه هستند
        # -----------------------------------------------------
        if all_same_size:
            item_dims = first
            count_items = len(items)

            # جعبه‌ها از کوچک به بزرگ
            boxes_sorted = sorted(
                boxes,
                key=lambda b: b["length"] * b["width"] * b["height"]
            )

            # کوچک‌ترین جعبه‌ای که کل آیتم‌ها جا می‌شوند
            for box in boxes_sorted:
                box_dims = (box["length"], box["width"], box["height"])
                max_fit = self.max_items_in_box(box_dims, item_dims)
                if max_fit >= count_items:
                    return [box]  # فقط همین جعبه کافی است

            # هیچ جعبه‌ای نتوانست جا بدهد
            return boxes

        # -----------------------------------------------------
        # 🟩 حالت عادی (منطق اصلی فیلتر خودت)
        # -----------------------------------------------------

        # بزرگ‌ترین ابعاد هر آیتم
        max_length = max(i["length"] for i in items)
        max_width  = max(i["width"]  for i in items)
        max_height = max(i["height"] for i in items)
        count_items = len(items)

        # مکعب فرضی
        cube = (max_length, max_width, max_height)

        # مرتب‌سازی جعبه‌ها بر اساس حجم (کوچک → بزرگ)
        def volume(b):
            return b["length"] * b["width"] * b["height"]

        boxes_sorted = sorted(boxes, key=volume)

        for i, box in enumerate(boxes_sorted):
            box_dims = (box["length"], box["width"], box["height"])
            max_fit = self.max_items_in_box(box_dims, cube)
            if max_fit >= count_items:
                return boxes_sorted[:i + 1]

        # اگر هیچ جعبه‌ای مناسب نبود → همه را برگردان
        return boxes_sorted
