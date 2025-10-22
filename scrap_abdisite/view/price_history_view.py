from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from ..models import WatchedURL, PriceHistory

def price_history_view(request, watched_id):
    watched = get_object_or_404(WatchedURL, id=watched_id)

    filter_type = request.GET.get('filter', 'week')
    start_date = None
    end_date = None

    if filter_type == 'week':
        start_date = timezone.now() - timedelta(days=7)
    elif filter_type == 'month':
        start_date = timezone.now() - timedelta(days=30)
    elif filter_type == 'custom':
        start_str = request.GET.get('start')
        end_str = request.GET.get('end')
        if start_str and end_str:
            start_date = timezone.datetime.fromisoformat(start_str)
            end_date = timezone.datetime.fromisoformat(end_str)

    queryset = PriceHistory.objects.filter(watched_url=watched)
    if start_date:
        queryset = queryset.filter(checked_at__gte=start_date)
    if end_date:
        queryset = queryset.filter(checked_at__lte=end_date)

    queryset = queryset.order_by('checked_at')

    context = {
        'watched': watched,
        'prices': queryset,
        'filter_type': filter_type,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'price_history.html', context)
