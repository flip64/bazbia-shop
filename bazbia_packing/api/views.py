# bazbiapacking/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bazbia_packing.api.serializers import PackingRequestSerializer


# اضافه کردن فیلترها 
from bazbia_packing.filters.volume_filter import VolumeFilter
from bazbia_packing.filters.one_item_filter import OneItemFilter
from bazbia_packing.filters.trim_largeboxes_filter import TrimLargeBoxesFilter

#from bazbia_packing.filters.dimension_filter import DimensionFilter
#from bazbia_packing.filters.weight_filter import WeightFilter
from bazbia_packing.models import ShippingBox

# فیلترهای مرحله‌ای
FILTERS = [OneItemFilter(),VolumeFilter() ,TrimLargeBoxesFilter()]

class PackingAPIView(APIView):

    def post(self, request):
        serializer = PackingRequestSerializer(data=request.data)
        if serializer.is_valid():
            items = serializer.validated_data['items']

            # خواندن جعبه‌ها از دیتابیس
            boxes_qs = ShippingBox.objects.filter(carton_type="پست")
            # تبدیل به دیکشنری برای استفاده در فیلترها
            boxes = [
                {
                    "name": box.name,
                    "length": box.length,
                    "width": box.width,
                    "height": box.height,
                    "max_weight": box.max_weight,
                    "carton_weight": box.carton_weight,
                    "carton_type": box.carton_type
                }
                for box in boxes_qs
            ]

            # اعمال فیلترها مرحله‌ای
            for f in FILTERS:
                print(boxes.)
                boxes = f.filter(boxes, items)
                if not boxes:
                    return Response(
                        {"error": "هیچ جعبه‌ای مناسب نیست."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                elif len(boxes) == 1:
                    return Response({"selected_box": boxes[0]})

            # اگر چند جعبه مناسب باقی مانده
            return Response({"possible_boxes": boxes})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
