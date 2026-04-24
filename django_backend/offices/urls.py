from rest_framework.routers import DefaultRouter
from .views import OfficeViewSet

router = DefaultRouter()
router.register("offices", OfficeViewSet, basename="office")

urlpatterns = router.urls
