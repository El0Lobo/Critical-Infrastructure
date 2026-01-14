from rest_framework.routers import DefaultRouter

from .views import AssetViewSet, CollectionViewSet

router = DefaultRouter()
router.register(r"assets", AssetViewSet, basename="api-assets")
router.register(r"collections", CollectionViewSet, basename="api-collections")

urlpatterns = router.urls
