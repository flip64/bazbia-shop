class OneItemFilter:
    def filter(self, boxes, items):
        """
        فیلتر کوچک‌ترین جعبه مناسب فقط برای یک آیتم.
        اگر لیست آیتم‌ها بیشتر از یک آیتم باشد، همه جعبه‌ها بدون فیلتر عبور می‌کنند.
        """

        if not items:
            return boxes  # اگر آیتمی نبود، همه جعبه‌ها مجازند

        if len(items) > 1:
            return boxes  # فقط یک آیتم مد نظر است، بیشتر از آن رد نمی‌شود

        item = items[0]  # فقط یک آیتم داریم

        def can_fit(box, item):
            """
            بررسی اینکه آیا آیتم در جعبه جا می‌شود با در نظر گرفتن چرخش
            """
            box_dims = sorted([box['length'], box['width'], box['height']])
            item_dims = sorted([item['length'], item['width'], item['height']])
            return all(i <= b for i, b in zip(item_dims, box_dims))

        # فیلتر جعبه‌های مناسب
        possible_boxes = [box for box in boxes if can_fit(box, item)]

        if not possible_boxes:
            return []  # هیچ جعبه‌ای مناسب نیست

        # کوچک‌ترین جعبه از نظر حجم
        best_box = min(possible_boxes, key=lambda b: b['length'] * b['width'] * b['height'])
        return [best_box]
