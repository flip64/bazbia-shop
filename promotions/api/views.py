# promotions/views.py
from rest_framework import viewsets
from .models import Banner
from .serializers import BannerSerializer

class BannerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Banner.objects.filter(active=True).order_by("created_at")
    serializer_class = BannerSerializer
