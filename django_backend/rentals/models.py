from django.db import models
from employees.models import Employee
from vehicles.models import Vehicle


class Rental(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name="rentals")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="rentals")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_time"]

    def __str__(self):
        return f"Rental #{self.pk} — {self.vehicle} ({self.status})"
