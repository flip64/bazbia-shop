from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from scrap_abdisite.models import WatchedURL, PriceHistory
from products.models import ProductVariant
from .serializers import WatchedURLSerializer, WatchedURLUpdatePriceSerializer

# کلید ثابت برای دسترسی به API
API_KEY = "my_secret_api_key_12345"


# ==============================
# API برای برگرداندن تمام WatchedURLها
# ==============================
def watched_urls_all_api(request):
    """
    API برگرداندن کل WatchedURLها با تمام جزئیات
    فقط با api_key معتبر
    """
    # کلید را می‌توان هم از query parameter گرفت و هم از header
    key = request.GET.get("api_key") or request.headers.get("X-API-KEY")
    if key != API_KEY:
        return JsonResponse({"error": "Invalid API key"}, status=401)

    # گرفتن لیست با روابط مرتبط
    watched_list = WatchedURL.objects.select_related(
        "variant", "variant__product", "supplier", "user"
    ).prefetch_related("history")

    # سریالایز داده‌ها
    serializer = WatchedURLSerializer(watched_list, many=True)
    return JsonResponse(
        {"count": len(serializer.data), "results": serializer.data},
        json_dumps_params={"ensure_ascii": False}
    )


# ==============================
# API برای بروزرسانی قیمت یک WatchedURL
# ==============================
class UpdateWatchedURLPriceAPIView(APIView):
    """
    API برای بروزرسانی قیمت WatchedURL با کلید API.
    همچنین به محض تغییر قیمت، واریانت مرتبط بروزرسانی می‌شود.
    """

    # چک کردن API Key
    def dispatch(self, request, *args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if api_key != API_KEY:
            return Response({"error": "کلید API معتبر نیست"}, status=status.HTTP_403_FORBIDDEN)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        try:
            watched_url = WatchedURL.objects.get(pk=pk)
        except WatchedURL.DoesNotExist:
            return Response({"error": "WatchedURL یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

        serializer = WatchedURLUpdatePriceSerializer(watched_url, data=request.data, partial=True)
        if serializer.is_valid():
            old_price = watched_url.price
            serializer.save()

            # ثبت PriceHistory فقط در صورت تغییر قیمت
            if old_price != watched_url.price:
                PriceHistory.objects.create(
                    watched_url=watched_url,
                    price=watched_url.price
                )

                # بروزرسانی قیمت واریانت (purchase_price)
                variant = watched_url.variant
                if variant:
                    variant.purchase_price = watched_url.price
                    variant.save(update_fields=['purchase_price'])

            return Response({"success": "قیمت بروزرسانی شد", "price": watched_url.price})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
