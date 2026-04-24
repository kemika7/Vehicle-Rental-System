from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from vehicle_rental.permissions import IsAdmin
from .filters import RentalFilter
from .models import Rental
from .serializers import RentalCreateSerializer, RentalUpdateSerializer, RentalDetailSerializer


class RentalViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RentalFilter
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        qs = Rental.objects.select_related("vehicle__office", "employee__office").all()
        user = self.request.user
        if user.role != "admin":
            qs = qs.filter(employee=user)
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return RentalCreateSerializer
        if self.action in ("partial_update", "update"):
            return RentalUpdateSerializer
        return RentalDetailSerializer

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAuthenticated(), IsAdmin()]
        return super().get_permissions()
