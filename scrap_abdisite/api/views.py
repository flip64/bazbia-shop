from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from scrap_abdisite.models import WatchedURL
from .serializers import WatchedURLSerializer


@login_required
def watched_urls_all_api(request):
    """API برگرداندن کل WatchedURLها با تمام جزئیات"""
    watched_list = WatchedURL.objects.select_related(
        "variant", "variant__product", "supplier", "user"
    ).prefetch_related("history")

    serializer = WatchedURLSerializer(watched_list, many=True)
    return JsonResponse(
        {"count": len(serializer.data), "results": serializer.data},
        safe=False,
        json_dumps_params={"ensure_ascii": False}
    )
