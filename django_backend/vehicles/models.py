from django.db import models
from offices.models import Office


class Vehicle(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        RENTED = "rented", "Rented"
        MAINTENANCE = "maintenance", "Maintenance"

    class VehicleType(models.TextChoices):
        CAR = "car", "Car"
        VAN = "van", "Van"
        TRUCK = "truck", "Truck"
        MOTORCYCLE = "motorcycle", "Motorcycle"

    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveSmallIntegerField()
    plate_number = models.CharField(max_length=20, unique=True)
    vehicle_type = models.CharField(max_length=20, choices=VehicleType.choices, default=VehicleType.CAR)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    office = models.ForeignKey(Office, on_delete=models.PROTECT, related_name="vehicles")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["make", "model"]

    def __str__(self):
        return f"{self.year} {self.make} {self.model} ({self.plate_number})"
