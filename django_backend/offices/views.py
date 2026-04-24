from rest_framework import viewsets
from vehicle_rental.permissions import IsAdminOrReadOnly
from .models import Office
from .serializers import OfficeSerializer


class OfficeViewSet(viewsets.ModelViewSet):
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer
    permission_classes = [IsAdminOrReadOnly]
