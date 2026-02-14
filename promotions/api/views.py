# promotions/views.py
from rest_framework import viewsets
from promotions.models import Banner
from promotions.api.serializers import BannerSerializer

class BannerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Banner.objects.filter(active=True).order_by("created_at")
    serializer_class = BannerSerializer
