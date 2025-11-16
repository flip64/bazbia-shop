import itertools

class FitByDimensionsFilter:
    def max_items_in_box(self, box_dims, item_dims):
        """
        محاسبه بیشترین تعداد آیتمی که در جعبه جا می‌شود (با چرخش)
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
        """
        بررسی آیتم‌ها دونه‌دونه و حذف جعبه‌هایی که آیتم در آن‌ها جا نمی‌شود.
        """
        if not boxes or not items:
            return []

        # مرتب‌سازی جعبه‌ها از کوچک به بزرگ
        boxes_sorted = sorted(boxes, key=lambda b: b['length'] * b['width'] * b['height'])
        remaining_boxes = boxes_sorted.copy()

        for item in items:
            item_dims = (item['length'], item['width'], item['height'])
            new_remaining = []

            for box in remaining_boxes:
                box_dims = (box['length'], box['width'], box['height'])
                if self.max_items_in_box(box_dims, item_dims) >= 1:
                    # آیتم در این جعبه جا شد → جعبه را نگه دار
                    new_remaining.append(box)
                # اگر جا نشد → جعبه حذف می‌شود

            remaining_boxes = new_remaining

            if not remaining_boxes:
                # اگر هیچ جعبه‌ای برای آیتم‌ها باقی نماند → خروجی خالی
                return []

        # جعبه‌هایی که برای همه آیتم‌ها مناسب هستند
        return remaining_boxes
