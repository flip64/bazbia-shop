from django.http import JsonResponse
from scrap_abdisite.models import WatchedURL
from .serializers import WatchedURLSerializer

# کلید ثابت برای دسترسی به API
API_KEY = "my_secret_api_key_12345"

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
