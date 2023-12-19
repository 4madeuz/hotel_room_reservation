from rest_framework.routers import DefaultRouter

from .views import ReservationViewSet, RoomViewSet

router = DefaultRouter()
router.register(r'rooms', RoomViewSet, basename='room')
router.register(r'reservations', ReservationViewSet, basename='reservation')

urlpatterns = router.urls
