from rest_framework.routers import DefaultRouter
from .views import BannerViewSet

router = DefaultRouter()
router.register(r'banners', BannerViewSet)

urlpatterns = router.urls
