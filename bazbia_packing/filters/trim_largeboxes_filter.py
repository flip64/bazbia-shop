class TrimLargeBoxesFilter:
    def filter(self, boxes, items):

        """
        فیلتر جعبه‌ها بر اساس مکعب فرضی برای بزرگ‌ترین آیتم‌ها
        و حذف جعبه‌های بزرگتر از کوچک‌ترین جعبه مناسب.
        """

        if not items:
            return boxes

        # 1) بزرگ‌ترین ابعاد هر آیتم
        max_length = max(i["length"] for i in items)
        max_width  = max(i["width"]  for i in items)
        max_height = max(i["height"] for i in items)

        # 2) تعداد مکعب‌ها = تعداد آیتم‌ها
        count = len(items)

        # 3) محاسبه حجم کل مکعب‌ها
        cube_volume = max_length * max_width * max_height * count

        # 4) پیدا کردن جعبه‌هایی که مکعب‌ها در آن‌ها جا می‌شوند
        valid_boxes = []
        for box in boxes:
            box_volume = box["length"] * box["width"] * box["height"]
            if (box["length"] >= max_length and
                box["width"]  >= max_width and
                box["height"] >= max_height):
                valid_boxes.append(box)

        if not valid_boxes:
            return []  # هیچ جعبه مناسبی وجود ندارد

        # 5) کوچک‌ترین جعبه مناسب بر اساس حجم
        def volume(b):
            return b["length"] * b["width"] * b["height"]

        smallest_box = min(valid_boxes, key=volume)
        smallest_volume = volume(smallest_box)

        # 6) حذف جعبه‌های بزرگ‌تر
        filtered_boxes = [b for b in valid_boxes if volume(b) <= smallest_volume]

        return filtered_boxes

