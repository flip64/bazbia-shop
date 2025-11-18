import itertools

class FitByDimensionsFilter:
    def can_fit_item_in_box(self, box_dims, item_dims):
        """
        محاسبه ابنکه ایتم در جعبه جا مبسود با نه 
        """
        box_dims = sorted(box_dims)
        item_dims = sorted(item_dims)


        L_box, W_box, H_box = box_dims
        l_item, w_item, h_item = item_dims
        return (
            L_box >= l_item and
            W_box >= w_item and
            H_box >= h_item
         )

    def filter(self, boxes, items):

        """
        بررسی آیتم‌ها دونه‌دونه و حذف جعبه‌هایی که آیتم در آن‌ها جا نمی‌شود.
        """
        if not boxes or not items:
            return []

        # مرتب‌سازی جعبه‌ها از کوچک به بزرگ
        boxes_sorted = sorted(boxes, key=lambda b: b['length'] * b['width'] * b['height'])
        
        remaining_boxes = boxes_sorted.copy()
        new_remainig = []

        for item in items:
            item_dims = (item['length'], item['width'], item['height'])
            for box in remaining_boxes:
              print("box" , box)
              box_dims = (box['length'], box['width'], box['height'])
              print(self.can_fit_item_in_box(box_dims, item_dims))
              if not self.can_fit_item_in_box(box_dims, item_dims):
                # اگر جا نشد → جعبه حذف می‌شود
                break  
            # آیتم در این جعبه جا شد → جعبه را نگه دار
            new_remainig.append(box)


            if not new_remainig:
                # اگر هیچ جعبه‌ای برای آیتم‌ها باقی نماند → خروجی خالی
                return []

        # جعبه‌هایی که برای همه آیتم‌ها مناسب هستند
        return new_remainig
