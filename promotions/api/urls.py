from rest_framework.routers import DefaultRouter
from promotions.views import BannerViewSet

router = DefaultRouter()
router.register(r'banners', BannerViewSet)

urlpatterns = router.urls
