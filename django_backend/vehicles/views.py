from django.db.models import Exists, OuterRef
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from vehicle_rental.permissions import IsAdminOrReadOnly
from .filters import VehicleFilter
from .models import Vehicle
from .serializers import VehicleSerializer


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.select_related("office").all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = VehicleFilter

    def get_queryset(self):
        qs = super().get_queryset()
        available_from = self.request.query_params.get("available_from")
        available_to = self.request.query_params.get("available_to")

        if available_from and available_to:
            # Import here to avoid circular import at module load
            from rentals.models import Rental

            overlapping = Rental.objects.filter(
                vehicle=OuterRef("pk"),
                status__in=["active", "reserved"],
                start_time__lt=available_to,
                end_time__gt=available_from,
            )
            qs = qs.filter(~Exists(overlapping))

        return qs
