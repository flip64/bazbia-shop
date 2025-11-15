from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bazbia_packing.api.serializers import PackingRequestSerializer
from bazbia_packing.models import ShippingBox

# تابع فیلتر که جعبه‌های مناسب را برمی‌گرداند
from bazbia_packing.filters.base_filters import filter_boxes

class PackingAPIView(APIView):

    def post(self, request):
        serializer = PackingRequestSerializer(data=request.data)
        if serializer.is_valid():
            items = serializer.validated_data['items']

            # خواندن جعبه‌ها از دیتابیس
            boxes_qs = ShippingBox.objects.filter(carton_type="پست")
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

            # فراخوانی تابع فیلتر
            possible_boxes = filter_boxes(boxes, items)

            if not possible_boxes:
                return Response(
                    {"error": "هیچ جعبه‌ای مناسب نیست."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif len(possible_boxes) == 1:
                return Response({"selected_box": possible_boxes[0]})

            # چند جعبه مناسب باقی مانده
            return Response({"possible_boxes": possible_boxes})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
