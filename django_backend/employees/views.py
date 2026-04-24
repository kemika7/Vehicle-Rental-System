from rest_framework import generics, viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from vehicle_rental.permissions import IsAdmin, IsAdminOrSelf
from .models import Employee
from .serializers import (
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    EmployeeSerializer,
    MeSerializer,
)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = Employee.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class MeView(generics.RetrieveAPIView):
    serializer_class = MeSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.select_related("office").all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_permissions(self):
        if self.action in ("retrieve", "partial_update", "update"):
            return [IsAuthenticated(), IsAdminOrSelf()]
        return super().get_permissions()
