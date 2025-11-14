class VolumeFilter:
    def filter(self, boxes, items):
        """
        فیلتر جعبه‌ها بر اساس حجم مجموع آیتم‌ها
        """

        items_volume = sum(
            i["length"] * i["width"] * i["height"]
            for i in items
        )

        filtered = []
        for box in boxes:
            box_volume = box["length"] * box["width"] * box["height"]
            if box_volume >= items_volume:
                filtered.append(box)

        return filtered
